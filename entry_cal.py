import datetime
import streamlit as st
import streamlit_calendar as st_calendar
from collections import Counter
import json # JSON操作のため
import os   # ファイルの存在確認のため
import uuid # 一意のIDを生成するため

# --- 定数定義 ---
DATA_FILE = "events_data.json" # イベントデータを保存するファイル名

# --- データ永続化関数 ---
def save_events_to_file(events):
    """イベントリストをJSONファイルに保存する"""
    serializable_events = []
    for event in events:
        serializable_event = event.copy()
        if 'id' not in serializable_event or serializable_event['id'] is None:
            serializable_event['id'] = str(uuid.uuid4())
        if 'date' in serializable_event and isinstance(serializable_event['date'], datetime.date):
            serializable_event['date'] = serializable_event['date'].isoformat()
        if 'deadline' in serializable_event and isinstance(serializable_event['deadline'], datetime.date):
            serializable_event['deadline'] = serializable_event['deadline'].isoformat()
        serializable_events.append(serializable_event)
    
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(serializable_events, f, ensure_ascii=False, indent=4)
    except IOError as e:
        st.error(f"エラー: イベントデータの保存に失敗しました。 {e}")

def load_events_from_file():
    """JSONファイルからイベントリストを読み込む"""
    if not os.path.exists(DATA_FILE):
        return [] # ファイルが存在しない場合は空のリストを返す
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            loaded_events_str = json.load(f)
            deserialized_events = []
            for event_str in loaded_events_str:
                # ISOフォーマット文字列をdatetime.dateオブジェクトに変換
                deserialized_event = event_str.copy()
                if 'date' in deserialized_event and isinstance(deserialized_event['date'], str):
                    try:
                        deserialized_event['date'] = datetime.date.fromisoformat(deserialized_event['date'])
                    except ValueError:
                        st.warning(f"警告: イベント「{deserialized_event.get('title', '(無題)')}」の日付形式が無効です。このイベントは読み込まれません。")
                        continue # 不正な形式のデータはスキップ
                if 'deadline' in deserialized_event and isinstance(deserialized_event['deadline'], str):
                    try:
                        deserialized_event['deadline'] = datetime.date.fromisoformat(deserialized_event['deadline'])
                    except ValueError:
                        st.warning(f"警告: イベント「{deserialized_event.get('title', '(無題)')}」の締切日形式が無効です。このイベントは読み込まれません。")
                        continue # 不正な形式のデータはスキップ
                deserialized_events.append(deserialized_event)
            return deserialized_events
    except (IOError, json.JSONDecodeError) as e:
        st.error(f"エラー: イベントデータの読み込みに失敗しました。 {e}")
        return [] 
    
# --- セッションステートの初期化 ---
if 'event_list' not in st.session_state:
    st.session_state.event_list = load_events_from_file()


if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'editing_event_id' not in st.session_state:
    st.session_state.editing_event_id = None
if 'should_clear_form' not in st.session_state:
    st.session_state.should_clear_form = True
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'load_event_to_form_flag' not in st.session_state:
    st.session_state.load_event_to_form_flag = False

# フォームの値を保持するためのキー
FORM_EVENT_NAME_KEY = 'form_event_name'
FORM_EVENT_DATE_KEY = 'form_event_date'
FORM_EVENT_DEADLINE_KEY = 'form_event_deadline'
FORM_EVENT_DESCRIPTION_KEY = 'form_event_description'
SELECTBOX_EVENT_SELECTION_KEY = 'selectbox_event_selection_key'


# フォームの初期値を設定 (クリア時や初回ロード時)
if st.session_state.should_clear_form:
    st.session_state[FORM_EVENT_NAME_KEY] = 'イベント名'
    st.session_state[FORM_EVENT_DATE_KEY] = datetime.date.today() + datetime.timedelta(days=7)
    st.session_state[FORM_EVENT_DEADLINE_KEY] = datetime.date.today()
    st.session_state[FORM_EVENT_DESCRIPTION_KEY] = ''
    st.session_state.should_clear_form = False
    st.session_state.edit_mode = False
    st.session_state.editing_event_id = None
    # selectbox の選択もリセットされるようにキーの値をNoneにする (次回描画時にindexが先頭になる)
    if SELECTBOX_EVENT_SELECTION_KEY in st.session_state:
         st.session_state[SELECTBOX_EVENT_SELECTION_KEY] = None


# 編集モードでイベントが選択された場合、フォームに値をロード
if st.session_state.load_event_to_form_flag and st.session_state.editing_event_id:
    event_to_load = next((ev for ev in st.session_state.event_list if ev.get('id') == st.session_state.editing_event_id), None)
    if event_to_load:
        st.session_state[FORM_EVENT_NAME_KEY] = event_to_load.get('title', '')
        st.session_state[FORM_EVENT_DATE_KEY] = event_to_load.get('date', datetime.date.today() + datetime.timedelta(days=7))
        st.session_state[FORM_EVENT_DEADLINE_KEY] = event_to_load.get('deadline', datetime.date.today())
        st.session_state[FORM_EVENT_DESCRIPTION_KEY] = event_to_load.get('description', '')
    st.session_state.load_event_to_form_flag = False


#お知らせ (変更なし、ただし日付がないイベントは適切に除外)
st.subheader("🔔 お知らせ")
with st.container(border=True):
    today = datetime.date.today()
    # 日付型が有効なイベントのみを対象とする
    valid_events_for_notice = [
        ev for ev in st.session_state.event_list 
        if isinstance(ev.get('deadline'), datetime.date) and isinstance(ev.get('date'), datetime.date)
    ]

    if not valid_events_for_notice: # お知らせ対象の有効なイベントがない場合
        st.info("現在、日付が有効な登録イベントはありません。")
    else:
        st.markdown("##### 申込締切情報")
        sorted_events_by_deadline = sorted(valid_events_for_notice, key=lambda x: x['deadline'])
        deadline_messages = []
        for ev in sorted_events_by_deadline:
            delta = ev['deadline'] - today
            deadline_str = ev['deadline'].strftime('%Y年%m月%d日')
            if delta.days < 0:
                deadline_messages.append(f"- 【{ev['title']}】: 申込締切済 ({deadline_str})")
            elif delta.days == 0:
                deadline_messages.append(f"- **【{ev['title']}】: 本日締切！** ({deadline_str}) 🏃")
            else:
                deadline_messages.append(f"- 【{ev['title']}】: 申込締切まであと **{delta.days}日** ({deadline_str})")
        if deadline_messages:
            st.markdown("\n".join(deadline_messages))
        else:
            st.info("申込締切情報のあるイベントはありません。")

        st.divider()
        st.markdown("##### イベント日の重複チェック")
        event_dates_only = [ev['date'] for ev in valid_events_for_notice] # お知らせ同様、有効なイベントのみ
        date_counts = Counter(event_dates_only)
        duplicate_found = False
        for date_val, count in date_counts.items():
            if count >= 2:
                st.warning(f"⚠️ **重複注意:** {date_val.strftime('%Y年%m月%d日')} には {count}件のイベントが予定されています。")
                duplicate_found = True
        if not duplicate_found:
            st.success("✅ 現在、日付が重複しているイベントはありません。")

# --- イベント選択UI --

def handle_event_selection_change():
    selected_tuple = st.session_state[SELECTBOX_EVENT_SELECTION_KEY]
    actual_selected_id = selected_tuple[1] if selected_tuple else None

    if actual_selected_id:
        st.session_state.editing_event_id = actual_selected_id
        st.session_state.edit_mode = True
        st.session_state.load_event_to_form_flag = True
        st.session_state.should_clear_form = False # 編集対象をロードするのでクリアしない
    else: # 「イベントを選択...」が選ばれた場合
        if st.session_state.edit_mode: # 編集モードから解除された場合のみフォームクリアを指示
            st.session_state.should_clear_form = True
        st.session_state.editing_event_id = None
        st.session_state.edit_mode = False


if st.session_state.event_list:
    event_options_for_selectbox = [("イベントを選択...", None)] + [
        (ev.get('title', f"無題 (ID:{ev.get('id', '')[:6]})"), ev.get('id'))
        for ev in st.session_state.event_list if ev.get('id')
    ]
    
    current_editing_id = st.session_state.get('editing_event_id')
    current_index = 0
    if current_editing_id:
        for i, option in enumerate(event_options_for_selectbox):
            if option[1] == current_editing_id:
                current_index = i
                break
    
    st.selectbox(
        "編集/削除するイベントを選択:",
        options=event_options_for_selectbox,
        format_func=lambda x: x[0], # (タイトル, ID) のタプルのタイトル部分を表示
        key=SELECTBOX_EVENT_SELECTION_KEY,
        on_change=handle_event_selection_change,
        index=current_index
    )
else:
    st.info("登録されているイベントはありません。")

# --- 入力フォーム ---
st.header("イベント情報入力")
event_name = st.text_input('イベント名', key=FORM_EVENT_NAME_KEY)
event_date = st.date_input('イベント日', key=FORM_EVENT_DATE_KEY, min_value=datetime.date(2000,1,1))
event_deadline = st.date_input('申込締切日', key=FORM_EVENT_DEADLINE_KEY, min_value=datetime.date(2000,1,1))
event_description = st.text_area('説明', key=FORM_EVENT_DESCRIPTION_KEY)

# --- ボタン処理 ---
if st.session_state.edit_mode and st.session_state.editing_event_id:
    current_form_title = st.session_state.get(FORM_EVENT_NAME_KEY) if st.session_state.get(FORM_EVENT_NAME_KEY) else "選択されたイベント"
    st.subheader(f"### ✏️ 現在編集中: {current_form_title}")

    col_update, col_delete, col_cancel = st.columns(3)
    with col_update:
        if st.button("🖋 更新"):
            if not st.session_state[FORM_EVENT_NAME_KEY]: # 簡単なバリデーション
                st.warning("イベント名を入力してください。")
            else:
                updated_event_data = {
                    'id': st.session_state.editing_event_id,
                    'title': st.session_state[FORM_EVENT_NAME_KEY],
                    'date': st.session_state[FORM_EVENT_DATE_KEY],
                    'deadline': st.session_state[FORM_EVENT_DEADLINE_KEY],
                    'description': st.session_state[FORM_EVENT_DESCRIPTION_KEY]
                }
                event_updated = False
                for i, ev in enumerate(st.session_state.event_list):
                    if ev.get('id') == st.session_state.editing_event_id:
                        st.session_state.event_list[i] = updated_event_data
                        event_updated = True
                        break
                if event_updated:
                    save_events_to_file(st.session_state.event_list)
                    st.success(f"イベント '{updated_event_data['title']}' が更新されました！")
                    st.session_state.should_clear_form = True
                    st.rerun()
                else:
                    st.error("更新対象のイベントが見つかりませんでした。")
    with col_delete:
        if st.button("イベントを削除する", type="primary"):
            id_to_delete = st.session_state.editing_event_id
            title_deleted = ""
            for ev in st.session_state.event_list: # 削除前のタイトル取得
                if ev.get('id') == id_to_delete:
                    title_deleted = ev.get('title', '(無題のイベント)')
                    break
            st.session_state.event_list = [ev for ev in st.session_state.event_list if ev.get('id') != id_to_delete]
            save_events_to_file(st.session_state.event_list)
            st.success(f"イベント '{title_deleted}' が削除されました！")
            st.session_state.should_clear_form = True
            st.rerun()
    with col_cancel:
        if st.button("キャンセル"):
            st.session_state.should_clear_form = True
            st.rerun()
else:
    if st.button('🆕 登録'):
        if not event_name:
             st.warning("イベント名を入力してください。")
        else:
            new_event_data = {
                'id': str(uuid.uuid4()),
                'title': event_name,
                'date': event_date,
                'deadline': event_deadline,
                'description': event_description
            }
            st.session_state.event_list.append(new_event_data)
            save_events_to_file(st.session_state.event_list)
            st.session_state.submitted = True
            st.session_state.should_clear_form = True
            st.rerun()

if st.session_state.submitted:
    st.success(f"'{event_name}' を登録しました！")
    st.session_state.submitted = False

# --- カレンダー表示エリア ---
col1, col2 = st.columns(2)

valid_events_for_calendar = [
    ev for ev in st.session_state.event_list 
    if isinstance(ev.get('date'), datetime.date) and isinstance(ev.get('deadline'), datetime.date)
]

calendar_events_deadline_display = []
for ev in valid_events_for_calendar:
    event_for_deadline_cal = {
        'title': f"締切: {ev['title']}",
        'start': ev['deadline'].isoformat(),
        'end': ev['deadline'].isoformat(),
        'allDay': True,
        'extendedProps': {'id': ev.get('id'), 'original_title': ev['title']}
    }
    if st.session_state.editing_event_id == ev.get('id'):
        event_for_deadline_cal['backgroundColor'] = 'tomato'
        event_for_deadline_cal['borderColor'] = 'red'
    calendar_events_deadline_display.append(event_for_deadline_cal)

with col1:
    st.subheader("イベント申込締切日")
    calendar_options_deadline = {
        "locale": "ja",
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,timeGridWeek,listWeek"},
        "initialView": "dayGridMonth", "height": "auto"
    }
    st_calendar.calendar(events=calendar_events_deadline_display, options=calendar_options_deadline, key="deadline_calendar")

calendar_events_date_display = []
for ev in valid_events_for_calendar:
    event_for_date_cal = {
        'title': ev['title'],
        'start': ev['date'].isoformat(),
        'end': ev['date'].isoformat(),
        'allDay': True,
        'extendedProps': {'id': ev.get('id'), 'original_title': ev['title']}
    }
    if st.session_state.editing_event_id == ev.get('id'):
        event_for_date_cal['backgroundColor'] = 'tomato'
        event_for_date_cal['borderColor'] = 'red'
    calendar_events_date_display.append(event_for_date_cal)

with col2:
    st.subheader("イベント日")
    calendar_options_event_date = {
        "locale": "ja",
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,timeGridWeek,listWeek"},
        "initialView": "dayGridMonth", "selectable": True, "height": "auto"
    }
    st_calendar.calendar(events=calendar_events_date_display, options=calendar_options_event_date, key="event_date_calendar")

st.divider()
st.subheader("Google カレンダーに送信")
if st.button("Googleカレンダーにイベントを送信"):
    # app.py を実行して、events_data.json の内容を Google カレンダーへ反映
    try:
        subprocess.run(["python", "app.py"], check=True)
        st.success(":チェックマーク_緑: Google カレンダーへの送信が完了しました！")
    except Exception as e:
        st.error(f":警告: Google カレンダーへの送信中にエラーが発生しました: {e}")
