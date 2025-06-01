import datetime
import streamlit as st
import streamlit_calendar as st_calendar
from collections import Counter
import json # JSON操作のため
import os   # ファイルの存在確認のため

# --- 定数定義 ---
DATA_FILE = "events_data.json" # イベントデータを保存するファイル名

# --- データ永続化関数 ---
def save_events_to_file(events):
    """イベントリストをJSONファイルに保存する"""
    serializable_events = []
    for event in events:
        # datetime.dateオブジェクトをISOフォーマット文字列に変換
        serializable_event = event.copy() # 元の辞書を変更しないようにコピー
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
        return [] # エラー時も空のリストを返す
    

# --- セッションステートの初期化 ---
if 'event_list' not in st.session_state: # アプリの初回ロードやリフレッシュ時のみ実行
    st.session_state.event_list = load_events_from_file()

# 他のセッションステート変数の初期化は既存のままでOK
if 'should_clear' not in st.session_state:
    st.session_state.should_clear = False
if 'clicked_event_original_title' not in st.session_state:
    st.session_state.clicked_event_original_title = None
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

#お知らせ
st.subheader("🔔 お知らせ")

with st.container(border=True): 
    today = datetime.date.today()

    if not st.session_state.event_list:
        st.info("現在登録されているイベントはありません。")
    else:
        # 申込締切日までの残り日数表示 
        st.markdown("##### 申込締切情報")
        
        # 締切日でソート（古い順・近い順）
        sorted_events_by_deadline = sorted(st.session_state.event_list, key=lambda x: x['deadline'])
        
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
        
        st.divider() # 区切り線

        # 同じ日付のイベント重複警告 
        st.markdown("##### イベント日の重複チェック")
        event_dates_only = [ev['date'] for ev in st.session_state.event_list]
        date_counts = Counter(event_dates_only)

        duplicate_found = False
        for date_val, count in date_counts.items():
            if count >= 2:
                st.warning(f"⚠️ **重複注意:** {date_val.strftime('%Y年%m月%d日')} には {count}件のイベントが予定されています。")
                duplicate_found = True
        
        if not duplicate_found:
            st.success("✅ 現在、日付が重複しているイベントはありません。")

event_name = st.text_input(
    'イベントの名前を入力してください。',
    value=st.session_state.get('cleared_event_name', 'イベント1'),
    key='event_name'  # ここはそのまま
)

event_date = st.date_input(
    'イベントの当日の日付を入力してください。',
    value=st.session_state.get('cleared_event_date', datetime.date.today() + datetime.timedelta(days=7)),
    key='event_date'
)

event_deadline = st.date_input(
    'イベントの申し込み締め切りを入力してください。',
    value=st.session_state.get('cleared_event_deadline', datetime.date.today()),
    key='event_deadline'
)

event_description = st.text_area(
    'イベントの説明を入力してください。',
    value=st.session_state.get('cleared_event_description', ''),
    key='event_description'
)

# --- イベント登録処理 ---
if st.button('イベントを登録する'):
    new_event_data = {
        'title': event_name,
        'date': event_date,       
        'deadline': event_deadline, 
        'description': event_description
    }
    st.session_state.event_list.append(new_event_data)
    
    save_events_to_file(st.session_state.event_list) #変更点をファイルに保存
    
    st.session_state.submitted = True
    st.session_state.should_clear = True
    st.rerun()

if st.session_state.submitted:
    if st.session_state.event_list:
        last_event_name = st.session_state.event_list[-1]['title']
        st.success(f"イベント '{last_event_name}' が登録されました！")
    st.session_state.submitted = False # 一度表示したらフラグをリセット

# --- カレンダー表示エリア ---
st.header("カレンダー")
col1, col2 = st.columns(2)


# 申込締切日カレンダー用のイベントリスト作成
calendar_events_deadline_display = []
for ev in st.session_state.event_list:
    event_for_deadline_cal = {
        'title': f"締切: {ev['title']}",
        'start': ev['deadline'].isoformat(),
        'end': ev['deadline'].isoformat(), # 終日イベント
        'allDay': True,
        'extendedProps': {'original_title': ev['title']}
    }
    # 強調表示
    if st.session_state.clicked_event_original_title == ev['title']:
        event_for_deadline_cal['backgroundColor'] = 'tomato'
        event_for_deadline_cal['borderColor'] = 'red'
        event_for_deadline_cal['textColor'] = 'white'
    else:
        event_for_deadline_cal['backgroundColor'] = '#3788D8' # デフォルトの色 (FullCalendarのデフォルトに近い色)
        event_for_deadline_cal['borderColor'] = '#3788D8'
        event_for_deadline_cal['textColor'] = 'white'


    calendar_events_deadline_display.append(event_for_deadline_cal)

with col1:
    st.subheader("イベント申込締切日")
    calendar_options_deadline = {
         "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listWeek",
        },
        "height": "auto",
        "initialView": "dayGridMonth",
    }
    st_calendar.calendar(
        events=calendar_events_deadline_display,
        options=calendar_options_deadline,
        key="deadline_calendar" # 一意のキーを設定
    )


# イベント日カレンダー用のイベントリスト作成
calendar_events_date_display = []
for ev in st.session_state.event_list:
    calendar_events_date_display.append({
        'title': ev['title'],
        'start': ev['date'].isoformat(),
        'end': ev['date'].isoformat(), # 終日イベント
        'allDay': True,
        'extendedProps': {'original_title': ev['title']} 
    })

with col2:
    st.subheader("イベント日")
    calendar_options_event_date = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listWeek",
        },
        "initialView": "dayGridMonth",
        "selectable": True,
        "height": "auto", 
        "eventClick": "function(info) { return info.event.extendedProps.original_title; }" # このJSは直接機能しない
    }
    # イベント日カレンダーのキーとコールバック処理
    clicked_event_on_date_calendar = st_calendar.calendar(
        events=calendar_events_date_display,
        options=calendar_options_event_date,
        key="event_date_calendar" # 一意のキーを設定
    )
