import datetime
import streamlit as st
import streamlit_calendar as st_calendar

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

# ❸ ウィジェット生成時に、前段階で用意した cleared_* があればそれを default として渡す-
if st.session_state.should_clear:
    st.session_state['cleared_event_name'] = f'イベント1'
    st.session_state['cleared_event_date'] = datetime.date(2025, 5, 1) 
    st.session_state['cleared_event_deadline'] = datetime.date(2025, 4, 1)
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
    value=st.session_state.get('cleared_event_date', datetime.date(2025, 5, 1)),
    key='event_date'
)

event_deadline = st.date_input(
    'イベントの申し込み締め切りを入力してください。',
    value=st.session_state.get('cleared_event_deadline', datetime.date(2025, 4, 1)),
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

with col1:
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

with col2:
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

# デバッグ用にセッションステートを表示（開発中に便利）
# st.write("Debug - Current clicked_event_original_title:", st.session_state.clicked_event_original_title)
# st.write("Debug - Event List:", st.session_state.event_list)