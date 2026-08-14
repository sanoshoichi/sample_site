# sample_site

## 共有DB対応の予定調整アプリ

このアプリは SQLite を使って、候補日と参加者の登録情報を共同で保存できます。

### 起動方法

```bash
cd /Users/shoichi/Desktop/develop/sample_site
python3 server.py
```

ブラウザで以下を開いて使います。

- 管理者: http://localhost:8000/admin.html
- 参加者: http://localhost:8000/index.html

同じサーバーにアクセスしている人同士で、データが共有されます。
本番公開する場合は、サーバーを外部公開可能な環境に置けば、誰でも参照可能です。