# 1. 必要なライブラリをインポート
import streamlit as st
from google.cloud import firestore
import datetime
import os

# 2. Firestoreクライアントの初期化 (変更なし)
try:
    key_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if key_path is None:
        st.error("環境変数 'GOOGLE_APPLICATION_CREDENTIALS' が設定されていません。")
        st.stop()
    db = firestore.Client.from_service_account_json(key_path)
except Exception as e:
    st.error(f"Firestoreクライアントの初期化に失敗: {e}")
    st.stop()

# --- UI要素の定義 ---
st.title("Firestore 書き込みテスト (コレクション指定可)")

# <<< ★★★ コレクション名入力欄を追加 ★★★ >>>
collection_name_input = st.text_input(
    "保存先コレクション名を入力",
    value="messages", # デフォルト値を 'messages' にしておく
    key="collection_name"
)

# 3つのテキスト入力欄を作成 (変更なし)
sender_input = st.text_input("送信者名を入力", key="sender")
receiver_input = st.text_input("受信者名を入力", key="receiver")
message_input = st.text_input("メッセージ内容を入力", key="message")

# 送信ボタンを作成 (変更なし)
send_button = st.button("Firestoreに送信")

# --- 送信ボタンが押された時の処理 ---
if send_button:
    st.write("--- 送信ボタンが押されました ---") # デバッグ用

    # 4. 入力された値を取得 (変更なし)
    sender_name = sender_input
    receiver_name = receiver_input
    message_content = message_input
    # <<< ★★★ 入力されたコレクション名も取得 ★★★ >>>
    target_collection_name = collection_name_input

    # 5. 入力チェック (コレクション名もチェック対象に追加)
    if sender_name and receiver_name and message_content and target_collection_name:
        st.write(f"入力値: コレクション='{target_collection_name}', 送信者='{sender_name}', 受信者='{receiver_name}', 内容='{message_content}'") # デバッグ用

        # 6. Firestoreに書き込む処理 (try...exceptで囲む)
        try:
            st.write(f"--- Firestore書き込み試行 (コレクション: {target_collection_name}) ---") # デバッグ用

            # <<< ★★★ コレクション名を指定してドキュメントを用意 ★★★ >>>
            # 以前は "messages" だった部分を、入力された変数 target_collection_name に変更
            doc_ref = db.collection(target_collection_name).document()

            # 6-2. 書き込むデータを作成 (変更なし)
            data_to_set = {
                'sender': sender_name,
                'receiver': receiver_name,
                'content': message_content,
                'timestamp': datetime.datetime.now(tz=datetime.timezone.utc) # UTCで時刻記録
            }
            st.write(f"書き込むデータ: {data_to_set}") # デバッグ用

            # 6-3. 実際にFirestoreに書き込み (変更なし)
            doc_ref.set(data_to_set)

            st.write("--- Firestore書き込み成功 ---") # デバッグ用
            st.success(f"コレクション '{target_collection_name}' への書き込みに成功しました！") # 成功メッセージにコレクション名を含める

        except Exception as e:
            # 書き込み中にエラーが起きた場合
            st.write(f"--- Firestore書き込み失敗: {e} ---") # デバッグ用
            st.error(f"コレクション '{target_collection_name}' への書き込み中にエラーが発生しました: {e}")

    else:
        # 入力が不足している場合
        st.warning("コレクション名、送信者名、受信者名、メッセージ内容をすべて入力してください。") # 警告メッセージを修正