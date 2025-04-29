import streamlit as st

if not st.experimental_user.is_logged_in:
    st.title("ログインが必要です")
    if st.button("Googleでログイン"):
        st.login()
    st.stop()
else:
    st.write(f"こんにちは、{st.experimental_user.name} さん！")
    st.write(f"メールアドレス: {st.experimental_user.email}")
    st.button("ログアウト", on_click=st.logout)

# ここに本来のアプリの処理を書く
