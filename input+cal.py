import datetime
import streamlit as st
import streamlit_calendar as st_calendar
from collections import Counter

# ❶ ウィジェット用のキーはそのまま使うけど、クリア用のフラグだけ別キーにする
if 'should_clear' not in st.session_state:
    st.session_state.should_clear = False

# ❷ もし should_clear が True なら、クリア処理（例として各フィールドを空に）を行い、
#     終わったらまた should_clear を False に戻す
if 'event_list' not in st.session_state:
    st.session_state.event_list = []


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


# ❸ ウィジェット生成時に、前段階で用意した cleared_* があればそれを default として渡す-
if st.session_state.should_clear:
    st.session_state['cleared_event_name'] = f'イベント1'
    st.session_state['cleared_event_date'] = datetime.date.today() + datetime.timedelta(days=7)
    st.session_state['cleared_event_deadline'] = datetime.date.today()
    st.session_state['cleared_event_description'] = ''
    st.session_state.should_clear = False

# ❸ ウィジェット生成時に、前段階で用意した cleared_* があればそれを default として渡す
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

# ❹ 登録ボタンが押されたときは、イベントを session_state.event_list に追加し、
#     クリア用のフラグ should_clear を True にする
if st.button('イベントを登録する'):
    new_event_data = {
        'title': event_name,
        'date': event_date,
        'deadline': event_deadline,
        'description': event_description
    }
    st.session_state.event_list.append(new_event_data)
    st.session_state.submitted = True
    st.session_state.should_clear = True
    st.rerun() # フォームクリアとカレンダー更新を即時反映

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


# デバッグ用にセッションステートを表示（開発中に便利）
# st.write("Debug - Current clicked_event_original_title:", st.session_state.clicked_event_original_title)
# st.write("Debug - Event List:", st.session_state.event_list)
