# UR通知くん 🏠

UR賃貸の空き情報をLINEでお知らせするサービスです。

## サービスURL
👉 https://ur-tsuchikun.jp

## 特徴
- 全国5,711駅対応
- 駅・間取り・家賃で絞り込み
- 新着物件が出たらLINEで即通知
- 無料プランあり・登録30秒

## 技術スタック
- Backend: FastAPI + PostgreSQL + SQLAlchemy
- 通知: LINE Messaging API
- 課金: Stripe
- インフラ: XServer VPS (Ubuntu 22.04)
- スクレイパー: requests + BeautifulSoup4

## 開発背景
UR賃貸の空き物件は人気が高く、こまめなチェックが必要。
そこでLINEで自動通知するサービスを個人で開発しました。
