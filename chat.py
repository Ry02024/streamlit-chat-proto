import streamlit as st
from google.cloud import firestore
import datetime
import os
import pytz
import re
import html

def show_chat(my_email, partner_email):
    """
    指定されたユーザー間のチャット機能を表示する
    
    Args:
        my_email: 自分のメールアドレス
        partner_email: チャット相手のメールアドレス
    """
    # ChatRoomの識別子を作成（メールアドレスを辞書順にソートして連結）
    emails = sorted([my_email, partner_email])
    chat_room_id = f"{emails[0]}_{emails[1]}"
    
    # Firestoreクライアントの初期化
    try:
        # 環境変数があれば引数なしで初期化できる
        db = firestore.Client()
    except Exception as e:
        try:
            # Streamlit Cloud用の初期化（secrets.tomlから認証情報を取得）
            firestore_creds_dict = st.secrets["firestore_credentials"].to_dict()
            private_key_value = st.secrets["GCP_PRIVATE_KEY"]
            formatted_private_key = private_key_value.replace('\\n', '\n')
            firestore_creds_dict["private_key"] = formatted_private_key
            db = firestore.Client.from_service_account_info(firestore_creds_dict)
        except Exception as e2:
            st.error(f"Firestoreクライアントの初期化に失敗: {e2}")
            st.stop()
    
    # --- カスタムCSSの定義 ---
    st.markdown("""
    <style>
    /* チャットメッセージ全体を囲むコンテナ */
    .message-container {
        width: 100%;
        margin-bottom: 10px;
        display: flex;
    }

    /* メッセージバブルの基本スタイル */
    .message-bubble {
        max-width: 75%;
        padding: 10px 15px;
        border-radius: 18px;
        word-wrap: break-word;
        position: relative;
    }

    /* 自分のメッセージ用コンテナ (右寄せ) */
    .my-message-container {
        justify-content: flex-end;
    }

    /* 自分のメッセージバブル */
    .my-message-bubble {
        background-color: #77c7ff;
        color: black;
        border-bottom-right-radius: 5px;
    }

    /* 相手のメッセージ用コンテナ (左寄せ) */
    .their-message-container {
         justify-content: flex-start;
    }

    /* 相手のメッセージバブル */
    .their-message-bubble {
        background-color: #f0f0f0;
        color: black;
        border-bottom-left-radius: 5px;
    }

    /* タイムスタンプのスタイル */
    .timestamp {
        font-size: 0.75em;
        color: grey;
        display: block;
        text-align: right;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- メッセージ履歴表示処理 ---
    try:
        jst = pytz.timezone('Asia/Tokyo')
        utc = pytz.utc

        # Firestoreからメッセージを取得
        messages_ref = db.collection("chat_rooms").document(chat_room_id).collection("messages")
        docs = list(messages_ref.order_by("timestamp", direction=firestore.Query.ASCENDING).stream())
        
        # メッセージを表示
        for doc in docs:
            msg = doc.to_dict()
            sender = msg.get('sender', '')
            content = msg.get('content', '')
            ts_obj = msg.get('timestamp')

            # タイムスタンプを処理
            timestamp_str_for_html = ""
            if isinstance(ts_obj, datetime.datetime):
                if ts_obj.tzinfo is None: ts_obj = utc.localize(ts_obj)
                ts_jst = ts_obj.astimezone(jst)
                timestamp_str_for_html = f"<span class='timestamp'>{ts_jst.strftime('%H:%M')}</span>"

            # 自分のメッセージかどうかを判定
            is_mine = (sender == my_email)

            # CSSクラスとコンテナクラスを決定
            container_class = "my-message-container" if is_mine else "their-message-container"
            bubble_class = "my-message-bubble" if is_mine else "their-message-bubble"

            # HTMLを構築
            escaped_content = html.escape(content)
            message_html = f"""
            <div class="message-container {container_class}">
                <div class="message-bubble {bubble_class}">
                    {escaped_content}
                    {timestamp_str_for_html}
                </div>
            </div>
            """
            # レンダリング
            st.markdown(message_html, unsafe_allow_html=True)

    except Exception as e:
        if "requires an index" in str(e).lower():
            st.error(f"メッセージの取得にエラーが発生しました。Firestoreでインデックスを作成する必要があります。")
            try:
                url_match = re.search(r"(https?://\S+)", str(e))
                if url_match:
                    st.markdown(f"こちらのリンクからインデックスを作成できます: [インデックス作成リンク]({url_match.group(1)})")
            except: pass
        else:
            st.error(f"メッセージの取得・表示中に予期せぬエラーが発生しました: {e}")

    # --- メッセージ入力 ---
    prompt = st.chat_input("メッセージを入力")

    if prompt:
        try:
            # メッセージをFirestoreに送信
            messages_ref = db.collection("chat_rooms").document(chat_room_id).collection("messages")
            messages_ref.add({
                'sender': my_email,
                'content': prompt,
                'timestamp': datetime.datetime.now(tz=datetime.timezone.utc)
            })
            st.rerun()
        except Exception as e:
            st.error(f"メッセージの送信に失敗しました: {e}")
