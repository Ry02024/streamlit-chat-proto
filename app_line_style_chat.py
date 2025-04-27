# 1. 必要なライブラリをインポート
import streamlit as st
from google.cloud import firestore
import datetime
import os
import pytz
import re # インデックスURL抽出用

# --- 固定ユーザー名の定義 ---
AGENT = "担当者"
VISITOR = "訪問者"
DEFAULT_ROLE = AGENT

# 2. Firestoreクライアントの初期化 (Streamlit Cloud Secretsを使用)
try:
    # 別のSecretから private_key 文字列を取得
    private_key_value = st.secrets["GCP_PRIVATE_KEY"]
    # ★重要★: Secretsから取得した文字列内のリテラルな "\\n" を実際の改行 "\n" に置換
    formatted_private_key = private_key_value.replace('\\n', '\n')
    # 取得した private_key を辞書に追加
    firestore_creds_dict["private_key"] = formatted_private_key

    # google-cloud-firestore は辞書から直接クライアントを初期化できる
    db = firestore.Client.from_service_account_info(firestore_creds_dict)

    st.sidebar.success("Firestore接続成功 (Secrets)") # デバッグ用

except KeyError:
    st.error("Streamlit Cloud Secrets に 'firestore_credentials' が設定されていません。")
    st.stop()
except Exception as e:
    st.error(f"Firestoreクライアントの初期化に失敗 (Secrets): {e}")
    st.stop()

# ... (以降のコードは同じ) ...

# --- カスタムCSSの定義 ---
# st.markdownを使ってCSSを注入
st.markdown("""
<style>
/* チャットメッセージ全体を囲むコンテナ */
.message-container {
    width: 100%;
    margin-bottom: 10px;
    display: flex; /* Flexboxを使って左右寄せを制御 */
}

/* メッセージバブルの基本スタイル */
.message-bubble {
    max-width: 75%; /* メッセージが長すぎないように */
    padding: 10px 15px;
    border-radius: 18px;
    word-wrap: break-word; /* 長い単語を折り返す */
    position: relative; /* タイムスタンプの位置調整用 */
}

/* 自分のメッセージ用コンテナ (右寄せ) */
.my-message-container {
    justify-content: flex-end; /* Flexアイテムを右端に寄せる */
}

/* 自分のメッセージバブル */
.my-message-bubble {
    background-color: #77c7ff; /* 明るい青色 (例) */
    color: black;
    border-bottom-right-radius: 5px; /* 右下の角を少し変える */
}

/* 相手のメッセージ用コンテナ (左寄せ) - デフォルトのflex */
.their-message-container {
     justify-content: flex-start; /* デフォルト */
}

/* 相手のメッセージバブル */
.their-message-bubble {
    background-color: #f0f0f0; /* 明るい灰色 (例) */
    color: black;
    border-bottom-left-radius: 5px; /* 左下の角を少し変える */
}

/* タイムスタンプのスタイル */
.timestamp {
    font-size: 0.75em; /* 小さく */
    color: grey;
    display: block; /* 改行して表示 */
    text-align: right; /* バブル内で右寄せ */
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)


# --- アプリのタイトル ---
st.title("チャット (左右寄せ)")

# --- 自分の役割を選択 ---
if 'my_role' not in st.session_state:
    st.session_state.my_role = None

if st.session_state.my_role is None:
    selected_role = st.radio(
        "あなたの役割を選択してください:",
        (AGENT, VISITOR),
        index=(0 if DEFAULT_ROLE == AGENT else 1),
        key="role_selector"
    )
    if st.button("チャット開始"):
        st.session_state.my_role = selected_role
        st.rerun()
else:
    my_role = st.session_state.my_role
    receiver_role = VISITOR if my_role == AGENT else AGENT

    st.info(f"あなたは **{my_role}** です。相手は **{receiver_role}** です。")
    if st.button("役割を再選択"):
        st.session_state.my_role = None
        st.rerun()

    # --- メッセージ履歴表示処理 ---
    try:
        jst = pytz.timezone('Asia/Tokyo')
        utc = pytz.utc

        # Firestoreからの読み込み (変更なし)
        # ... (query1, query2, データ取得・ソート) ...
        query1 = db.collection("messages").where(filter=firestore.And([firestore.FieldFilter("sender", "==", my_role),firestore.FieldFilter("receiver", "==", receiver_role)])).order_by("timestamp", direction=firestore.Query.ASCENDING)
        query2 = db.collection("messages").where(filter=firestore.And([firestore.FieldFilter("sender", "==", receiver_role),firestore.FieldFilter("receiver", "==", my_role)])).order_by("timestamp", direction=firestore.Query.ASCENDING)
        docs1 = list(query1.stream())
        docs2 = list(query2.stream())
        min_utc_time = datetime.datetime.min.replace(tzinfo=utc)
        all_docs_combined = []
        for doc in docs1 + docs2:
            doc_data = doc.to_dict()
            if 'timestamp' not in doc_data or doc_data['timestamp'] is None: doc_data['timestamp'] = min_utc_time
            all_docs_combined.append(doc_data)
        all_messages = sorted(all_docs_combined, key=lambda x: x.get('timestamp', min_utc_time))


        # --- カスタムHTML/CSSで履歴を表示 ---
        for msg in all_messages:
            sender = msg.get('sender', '不明')
            content = msg.get('content', '')
            ts_obj = msg.get('timestamp')

            timestamp_str_for_html = ""
            if isinstance(ts_obj, datetime.datetime):
                if ts_obj.tzinfo is None: ts_obj = utc.localize(ts_obj)
                ts_jst = ts_obj.astimezone(jst)
                timestamp_str_for_html = f"<span class='timestamp'>{ts_jst.strftime('%H:%M')}</span>"

            # 自分のメッセージかどうかを判定
            is_mine = (sender == my_role)

            # CSSクラスとコンテナクラスを決定
            container_class = "my-message-container" if is_mine else "their-message-container"
            bubble_class = "my-message-bubble" if is_mine else "their-message-bubble"

            # HTMLを構築
            # 特殊文字をエスケープ (重要！)
            import html
            escaped_content = html.escape(content)

            message_html = f"""
            <div class="message-container {container_class}">
                <div class="message-bubble {bubble_class}">
                    {escaped_content}
                    {timestamp_str_for_html}
                </div>
            </div>
            """
            # st.markdownでHTMLとしてレンダリング
            st.markdown(message_html, unsafe_allow_html=True)

    except Exception as e:
         # (エラー処理は変更なし)
         if "requires an index" in str(e).lower():
             st.error(f"メッセージの取得にエラーが発生しました。Firestoreでインデックスを作成する必要があります。")
             try:
                 url_match = re.search(r"(https?://\S+)", str(e))
                 if url_match:
                     st.markdown(f"こちらのリンクからインデックスを作成できます: [インデックス作成リンク]({url_match.group(1)})")
             except: pass
         else:
             st.error(f"メッセージの取得・表示中に予期せぬエラーが発生しました: {e}")

    # --- メッセージ入力 (st.chat_input) ---
    prompt = st.chat_input("メッセージを入力")

    if prompt:
        try:
            doc_ref = db.collection("messages").document()
            doc_ref.set({
                'sender': my_role,
                'receiver': receiver_role,
                'content': prompt,
                'timestamp': datetime.datetime.now(tz=datetime.timezone.utc)
            })
            st.rerun()
        except Exception as e:
            st.error(f"メッセージの送信に失敗しました: {e}")