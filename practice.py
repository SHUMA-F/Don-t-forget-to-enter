import streamlit as st
import datetime 

st.title('Hello, Streamlit!')
 
st.write('変数を設-定')
count = 0
 
if 'count' not in st.session_state:
    st.session_state.count = 0
 
if st.button('push me'):
    st.write('ボタンを押しました')
    st.session_state.count += 1
 
st.write('count = ', st.session_state.count)

d = st.date_input('誕生日を入力してください。', datetime.date(1998, 2, 16))
st.write('私の誕生日は：', d)
st.write('ですね！')
