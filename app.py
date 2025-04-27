import streamlit as st
from google.cloud import firestore
import datetime
import pandas as pd
import os
import pytz # 日本時間変換のためインポート (requirements.txt に記載)

# --- Firestore クライアントの初期化 ---
# 環境変数 GOOGLE_APPLICATION_CREDENTIALS から認証情報を読み込む
# Codespaces Secrets経由で設定されていることを想定
try:
    # 環境変数からサービスアカウントキーファイルのパスを取得
    key_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if key_path is None:
        st.error("環境変数 'GOOGLE_APPLICATION_CREDENTIALS' が設定されていません。")
        st.info("GitHub Codespaces Secrets に 'GCP_SA_KEY_JSON' を設定し、ターミナルで `export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-key.json` のように設定してください。")
        st.stop()

    # 実際にキーファイルが存在するか確認 (デバッグ用)
    # if not os.path.exists(key_path):
    #     st.warning(f"指定されたサービスアカウントキーファイルが見つかりません: {key_path}")
        # ここで停止するかどうかは状況による

    db = firestore.Client.from_service_account_json(key_path)
    # または、環境変数だけ設定されていれば引数なしでも動作するはず
    # db = firestore.Client()

    # Firestoreに接続できるか簡単なテスト (任意)
    # try:
    #    db.collection('ping').document('test').set({'timestamp': firestore.SERVER_TIMESTAMP})
    #    st.sidebar.success("Firestoreに接続成功")
    # except Exception as ping_error:
    #    st.sidebar.error(f"Firestore接続テスト失敗: {ping_error}")

except Exception as e:
    st.error(f"Firestoreクライアントの初期化に失敗しました。")
    st.error(f"エラー詳細: {e}")
    st.info("サービスアカウントキーのパスや内容、IAM権限を確認してください。")
    st.stop() # エラー発生時はアプリを停止

# --- アプリのタイトル ---
st.title("Streamlit 簡易チャット (プロトタイプ)")
st.caption("※リアルタイム更新や暗号化はありません。メッセージは送信時や手動リロードで表示更新されます。")

# --- ユーザー名の入力 (セッション状態で保持) ---
if 'my_username' not in st.session_state:
    st.session_state.my_username = ""
if 'receiver_username' not in st.session_state:
    st.session_state.receiver_username = ""

# text_inputのコールバックでsession_stateを更新する
def update_username(key):
    st.session_state[key] = st.session_state[key + "_input"]

my_username = st.text_input(
    "あなたの名前",
    value=st.session_state.my_username,
    key="my_username_input",
    on_change=update_username,
    args=("my_username",)
)
receiver_username = st.text_input(
    "相手の名前",
    value=st.session_state.receiver_username,
    key="receiver_username_input",
    on_change=update_username,
    args=("receiver_username",)
)

# --- メッセージ履歴表示エリア ---
st.subheader("メッセージ履歴")
# プレースホルダーを使って後で内容を更新
message_history_placeholder = st.empty()

# --- メッセージ入力と送信ボタン ---
new_message = st.text_input("メッセージを入力", key="new_message_input")
send_button = st.button("送信")

# --- メッセージ送信処理 ---
if send_button and new_message and st.session_state.my_username and st.session_state.receiver_username:
    if st.session_state.my_username == st.session_state.receiver_username:
        st.warning("自分自身にはメッセージを送信できません。")
    else:
        try:
            # Firestoreの 'messages' コレクションにドキュメントを追加
            doc_ref = db.collection("messages").document() # 自動IDでドキュメント作成
            doc_ref.set({
                'sender': st.session_state.my_username,
                'receiver': st.session_state.receiver_username,
                'content': new_message,
                'timestamp': datetime.datetime.now(tz=datetime.timezone.utc) # 必ずUTCでタイムスタンプ保存
            })
            st.success("メッセージを送信しました！")
            # メッセージ入力欄をクリアするために session_state を更新し、再実行をトリガー
            # st.session_state.new_message_input = ""
            st.rerun() # 再実行して表示を即時更新

        except Exception as e:
            st.error(f"メッセージの送信に失敗しました: {e}")

# --- メッセージ送信処理 ---
# <<< ★★★ デバッグコード追加 ★★★ >>>
st.write("--- スクリプト実行チェック ---") # スクリプトが実行されているか確認
if send_button:
    st.write(f"--- 送信ボタンが押されました ---")
    st.write(f"入力されたメッセージ: '{new_message}'")
    st.write(f"送信者 (session_state): '{st.session_state.my_username}'")
    st.write(f"受信者 (session_state): '{st.session_state.receiver_username}'")

# 元の if 条件
if send_button and new_message and st.session_state.my_username and st.session_state.receiver_username:
    st.write("--- 送信条件を満たしました ---") # ★デバッグ追加

    if st.session_state.my_username == st.session_state.receiver_username:
        st.warning("自分自身にはメッセージを送信できません。")
        st.write("--- 自分自身への送信のためスキップ ---") # ★デバッグ追加
    else:
        st.write("--- Firestore書き込み試行ブロック開始 ---") # ★デバッグ追加
        try:
            st.write("--- db.collection('messages').document() 実行 ---") # ★デバッグ追加
            doc_ref = db.collection("messages").document()

            data_to_set = {
                'sender': st.session_state.my_username,
                'receiver': st.session_state.receiver_username,
                'content': new_message,
                'timestamp': datetime.datetime.now(tz=datetime.timezone.utc)
            }
            st.write(f"--- 書き込むデータ: {data_to_set} ---") # ★デバッグ追加

            st.write("--- doc_ref.set() 実行 ---") # ★デバッグ追加
            doc_ref.set(data_to_set)
            st.write("--- Firestore書き込み成功 ---") # ★デバッグ追加

            st.success("メッセージを送信しました！")
            st.write("--- st.rerun() 実行前 ---") # ★デバッグ追加
            st.rerun()

        except Exception as e:
            st.write(f"--- Firestore書き込み失敗: {e} ---") # ★デバッグ追加
            st.error(f"メッセージの送信に失敗しました: {e}")

    st.write("--- 送信処理終了 ---") # ★デバッグ追加
# <<< ★★★ デバッグコードここまで ★★★ >>>
# else: # 名前が片方または両方未入力の場合は、message_display_content は初期値のまま

# プレースホルダーに最終的なメッセージ履歴内容を表示
message_history_placeholder.text_area("履歴", value=message_display_content, height=300, key="message_history_display", disabled=True)

# --- データログ表示 ---
st.subheader("データログ (Firestoreの内容)")
# データログは、all_docs_data リストにデータが入っている場合のみ表示
if all_docs_data: # all_docs_data は上の if ブロック内で更新される
    try:
        # ... (DataFrame 表示処理 - ここは変更なし) ...
        df = pd.DataFrame(all_docs_data)
        # ... (列選択、タイムスタンプフォーマットなど) ...
        if 'timestamp' in df.columns:
             # ... (タイムスタンプ処理) ...
             df['timestamp_jst'] = df['timestamp'].apply(format_timestamp_for_log) # format_timestamp_for_log 関数は定義済みとする
             final_columns = ['timestamp_jst', 'sender', 'receiver', 'content', 'id', 'timestamp']
             df_display = df[[col for col in final_columns if col in df.columns]]
             if 'timestamp' in df_display.columns:
                  df_display = df_display.sort_values(by='timestamp', ascending=True)
        else:
             df_display = df[['sender', 'receiver', 'content', 'id']] # idも表示

        st.dataframe(df_display)

    except Exception as e:
        st.error(f"データログの表示中にエラーが発生しました: {e}")
        st.write("生データ:")
        st.json(all_docs_data)
else:
    # ユーザー名が両方入力されていて、かつデータがない場合のみ「データなし」と表示
    if st.session_state.my_username and st.session_state.receiver_username:
        st.write("表示するデータログはありません。")
    # else: # 名前が未入力の場合は何も表示しない（または別のメッセージ）
    #     pass

# --- (おまけ) 手動更新ボタン ---
# (これは変更なし) 