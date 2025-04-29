import streamlit as st
import chat  # チャット機能をインポート

# 許可するメールアドレスのリスト
allowed_emails = ["tan0ry0@gmail.com", "tan0ry02024@example.com"]

# サイドバーにアプリ情報を表示
st.sidebar.title("チャットアプリ")
st.sidebar.info("Google認証でログインして、チャットを楽しめます")

# ログイン処理
if not st.user.is_logged_in:
    st.title("ログインが必要です")
    st.write("このチャットアプリはログインが必要です。Googleアカウントでログインしてください。")
    if st.button("Googleでログイン"):
        st.login()
    st.stop()
else:
    # メールアドレスによるアクセス制御
    if st.user.email not in allowed_emails:
        st.error("アクセス権がありません")
        st.button("ログアウト", on_click=st.logout)
        st.stop()
    
    # ログイン成功後の処理
    st.title("チャットアプリへようこそ！")
    st.write(f"こんにちは、{st.user.name} さん！")
    
    # チャット相手の選択肢
    # ここでは固定の相手を例示していますが、Firestoreから許可ユーザーリストを取得するなどの拡張も可能
    if "chat_partner" not in st.session_state:
        st.session_state.chat_partner = None
    
    if st.session_state.chat_partner is None:
        st.subheader("チャット相手を選択してください")
        partners = [email for email in allowed_emails if email != st.user.email]
        
        if not partners:
            st.warning("チャット相手が登録されていません")
        else:
            selected_partner = st.selectbox("チャット相手", partners)
            if st.button("チャットを開始"):
                st.session_state.chat_partner = selected_partner
                st.rerun()
    else:
        # チャット機能を表示
        partner = st.session_state.chat_partner
        st.subheader(f"{partner} とのチャット")
        
        if st.button("相手を変更"):
            st.session_state.chat_partner = None
            st.rerun()
        
        # チャット機能を呼び出し
        chat.show_chat(my_email=st.user.email, partner_email=partner)
