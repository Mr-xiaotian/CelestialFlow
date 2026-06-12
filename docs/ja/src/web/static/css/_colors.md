# _colors.css

> 📅 最終更新日: 2026/05/23

CSS Variables (`:root`) をベースにした Web UI のグローバルカラーシステム変数を定義し、統一管理とテーマ切り替えを容易にします。

## カラー体系

プロジェクトはマルチカラーレベル設計を採用し、各カラー系統は 50 から 900 までの複数のレベルを含みます。

### コアカラー系統

- **フロスト (Frost)**: `--frost-0` (#ffffff)。背景と純白要素に使用。
- **カーボン (Carbon)**: `--carbon-50` ~ `--carbon-900`。テキスト、ボーダー、シャドウ、ダークモード背景に使用。
- **ジェイド (Jade)**: `--jade-50` ~ `--jade-900`。成功状態、プログレスバー、ポジティブフィードバックに使用。
- **クリムゾン (Crimson)**: `--crimson-50` ~ `--crimson-900`。エラー状態、異常アラート、ネガティブフィードバックに使用。
- **マリーゴールド (Marigold)**: `--marigold-50` ~ `--marigold-900`。重複タスク、警告、ニュートラル状態に使用。
- **コーンフラワー (Cornflower)**: `--cornflower-50` ~ `--cornflower-900`。実行中状態、リンク、主要アクションボタンに使用。

### 補助カラー系統

- **アンバー (Amber)**: `--amber-50` ~ `--amber-900`。
- **ローズ (Rose)**: `--rose-50` ~ `--rose-900`。
- **バイオレット (Violet)**: `--violet-50` ~ `--violet-900`。
- **スカイ (Sky)**: `--sky-50` ~ `--sky-900`。

## 使用方法

他の CSS ファイルで `var()` 関数を通じて参照します：

```css
.example {
  color: var(--carbon-900);
  background-color: var(--jade-50);
  border: 1px solid var(--cornflower-500);
}
```

## デザイン仕様

- **テキスト色**: デフォルトで `--carbon-900`（ライトモード）または `--carbon-200`（ダークモード）を使用。
- **ボーダー色**: 通常 `--carbon-200` または `--carbon-300` を使用。
- **状態色**:
  - 成功: `Jade`
  - エラー: `Crimson`
  - 重複: `Marigold`
  - 実行中: `Cornflower`
  - 待機/停止: `Carbon`
