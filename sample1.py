import datetime
import streamlit as st
import streamlit_calendar as st_calendar
from collections import Counter

# ---------------- セッション初期化 ----------------
DEFAULT_NAME = "イベント1"
for key, default in {
    'should_clear': False,
    'event_list': [],
    'submitted': False,
    'edit_mode': False,
    'edit_idx': None,
    'cal_ver': 0,
    'selected_title': None,  # ← 直近クリックした元タイトル
}.items():
    st.session_state.setdefault(key, default)

# ---------------- お知らせ ----------------
st.subheader("🔔 お知らせ")
with st.container(border=True):
    today = datetime.date.today()
    if not st.session_state.event_list:
        st.info("現在登録されているイベントはありません。")
    else:
        st.markdown("##### 申込締切情報")
        for ev in sorted(st.session_state.event_list, key=lambda x: x['deadline']):
            remain = (ev['deadline'] - today).days
            dl_str = ev['deadline'].strftime('%Y年%m月%d日')
            if remain < 0:
                st.write(f"- 【{ev['title']}】: 申込締切済 ({dl_str})")
            elif remain == 0:
                st.write(f"- **【{ev['title']}】: 本日締切！** ({dl_str}) 🏃")
            else:
                st.write(f"- 【{ev['title']}】: 申込締切まであと **{remain}日** ({dl_str})")
        st.divider()
        st.markdown("##### イベント日の重複チェック")
        dup_flag = False
        for d, c in Counter(e['date'] for e in st.session_state.event_list).items():
            if c >= 2:
                st.warning(f"⚠️ **重複注意:** {d.strftime('%Y年%m月%d日')} に {c}件のイベント")
                dup_flag = True
        if not dup_flag:
            st.success("✅ 日付が重複しているイベントはありません。")

# ---------------- フォームデフォルト ----------------
if st.session_state.should_clear:
    st.session_state.cleared_event = {
        'title': DEFAULT_NAME,
        'date': datetime.date.today() + datetime.timedelta(days=7),
        'deadline': datetime.date.today(),
        'description': ''
    }
    st.session_state.should_clear = False

if st.session_state.edit_mode and st.session_state.edit_idx is not None:
    base_ev = st.session_state.event_list[st.session_state.edit_idx]
else:
    base_ev = st.session_state.get('cleared_event', {
        'title': DEFAULT_NAME,
        'date': datetime.date.today() + datetime.timedelta(days=7),
        'deadline': datetime.date.today(),
        'description': ''
    })

# ---------------- 現在選択中ラベル & 手動選択 ----------------
if st.session_state.event_list:
    titles = [ev['title'] for ev in st.session_state.event_list]
    default_idx = titles.index(st.session_state.selected_title) if st.session_state.selected_title in titles else 0
    sel = st.selectbox("編集するイベントを選択", titles, index=default_idx, key="title_selector")
    # セレクタで選ばれたら強制的にそのイベントに切替 (クリックと同じロジック)
    if sel != st.session_state.selected_title:
        st.session_state.selected_title = sel
        for i, ev in enumerate(st.session_state.event_list):
            if ev['title'] == sel:
                st.session_state.edit_mode = True
                st.session_state.edit_idx = i
                st.session_state.should_clear = False
                st.rerun()
else:
    st.markdown("### 🆕 新規イベントを作成")

# ラベル表示
if st.session_state.selected_title:
    st.markdown(f"### ✏️ 現在編集中: **{st.session_state.selected_title}**")

# ---------------- 入力フォーム ---------------- ---------------- ---------------- ----------------
with st.form("event_form"):
    event_name = st.text_input('イベント名', value=base_ev['title'])
    event_date = st.date_input('イベント日', value=base_ev['date'])
    event_deadline = st.date_input('申込締切日', value=base_ev['deadline'])
    event_description = st.text_area('説明', value=base_ev['description'])

    col_reg, col_upd, col_new = st.columns(3)
    register_btn = col_reg.form_submit_button("🆕 登録", disabled=st.session_state.edit_mode)
    update_btn   = col_upd.form_submit_button("🖋 更新", disabled=not st.session_state.edit_mode)
    new_btn      = col_new.form_submit_button("➕ 新規", disabled=not st.session_state.edit_mode)

# ---------------- ボタン処理 ----------------
if register_btn:
    st.session_state.event_list.append({
        'title': event_name,
        'date': event_date,
        'deadline': event_deadline,
        'description': event_description
    })
    st.success(f"'{event_name}' を登録しました！")
    st.session_state.should_clear = True
    st.session_state.cal_ver += 1
    st.rerun()

if update_btn and st.session_state.edit_mode and st.session_state.edit_idx is not None:
    idx = st.session_state.edit_idx
    st.session_state.event_list[idx] = {
        'title': event_name,
        'date': event_date,
        'deadline': event_deadline,
        'description': event_description
    }
    st.success(f"'{event_name}' を更新しました！")
    st.session_state.edit_mode = False
    st.session_state.edit_idx = None
    st.session_state.should_clear = True
    st.session_state.cal_ver += 1
    st.rerun()

if new_btn and st.session_state.edit_mode:
    st.session_state.edit_mode = False
    st.session_state.edit_idx = None
    st.session_state.should_clear = True
    st.rerun()

# ---------------- カレンダー表示 ----------------
st.header('カレンダー')
col1, col2 = st.columns(2)

def make_event(ev, idx, for_deadline=False):
    data = {
        'title': f"締切: {ev['title']}" if for_deadline else ev['title'],
        'start': (ev['deadline'] if for_deadline else ev['date']).isoformat(),
        'allDay': True,
        'extendedProps': {
            'idx': idx,
            'original_title': ev['title']
        }
    }
    return data

deadline_events = [make_event(e, i, True) for i, e in enumerate(st.session_state.event_list)]
with col1:
    st.subheader('申込締切')
    click_deadline = st_calendar.calendar(deadline_events, {
        'headerToolbar': {'left':'prev,next today','center':'title','right':'dayGridMonth,timeGridWeek,listWeek'},
        'initialView':'dayGridMonth',
        'height':'auto'
    }, key=f'dl_cal_{st.session_state.cal_ver}')

date_events = [make_event(e, i, False) for i, e in enumerate(st.session_state.event_list)]
with col2:
    st.subheader('イベント日')
    click_date = st_calendar.calendar(date_events, {
        'headerToolbar': {'left':'prev,next today','center':'title','right':'dayGridMonth,timeGridWeek,listWeek'},
        'initialView':'dayGridMonth',
        'selectable': True,
        'height':'auto'
    }, key=f'dt_cal_{st.session_state.cal_ver}')

# ---------------- クリック処理 ----------------

def process_click(cal_res):
    """クリックイベント → 常にラベル更新・必要なら edit_idx 更新"""
    if not cal_res or not cal_res.get('eventsSet') or not cal_res['eventsSet'].get('events'):
        return
    ev = cal_res['eventsSet']['events'][0]
    # 元タイトルは extendedProps.original_title があれば優先
    ev_title = ev.get('extendedProps', {}).get('original_title', ev.get('title', ''))
    idx = ev.get('extendedProps', {}).get('idx')
    if idx is None:
        # フォールバック探索
        date_key = datetime.date.fromisoformat(ev.get('start')[:10])
        for i, e in enumerate(st.session_state.event_list):
            if e['title'] == ev_title and e['date'] == date_key:
                idx = i
                break
    if idx is None:
        return
    idx = int(idx)

    # ラベルは毎クリック更新
    st.session_state.selected_title = ev_title

    # idx が変わった時だけフォーム内容を切り替える
    if idx != st.session_state.edit_idx or not st.session_state.edit_mode:
        st.session_state.edit_mode = True
        st.session_state.edit_idx = idx
        st.session_state.should_clear = False
        st.rerun()

process_click(click_date)
process_click(click_deadline)
