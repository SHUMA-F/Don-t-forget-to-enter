import datetime
import streamlit as st
import streamlit_calendar as st_calendar

# ❶ ウィジェット用のキーはそのまま使うけど、クリア用のフラグだけ別キーにする
if 'should_clear' not in st.session_state:
    st.session_state.should_clear = False

# ❷ もし should_clear が True なら、クリア処理（例として各フィールドを空に）を行い、
#     終わったらまた should_clear を False に戻す
if st.session_state.should_clear:
    # ウィジェットのキーと同じキー名に session_state を直接上書きしようとするとエラーになるから、
    # form_clear 用の別キーに新しい初期値を用意しておいて、その値を使うようにする
    # ここでは「クリア用に別のキー」を利用する方法にする
    st.session_state['cleared_event_name'] = 'イベント1'  
    st.session_state['cleared_event_date'] = datetime.date(2025, 5, 1)
    st.session_state['cleared_event_deadline'] = datetime.date(2025, 4, 1)
    st.session_state['cleared_event_description'] = ''
    # クリア処理が終わったら flag をリセット
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
    event1 = {
        'title': event_name,
        'start': event_date.isoformat(),
        'end': event_date.isoformat(),
        'description': event_description
    }
    if 'event_list' not in st.session_state:
        st.session_state.event_list = []
    st.session_state.event_list.append(event1)
    st.session_state.submitted = True

    # 次の実行サイクルでフォームをクリアしたいのでフラグを立てる
    st.session_state.should_clear = True

if st.session_state.get('submitted', False):
    st.success(f"イベント '{event_name}' が登録されました！")

# カレンダー表示
cal = st_calendar.calendar(events=st.session_state.get('event_list', []))
st.write(cal)
