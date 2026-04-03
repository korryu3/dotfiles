# テストのアンチパターン

モックの追加やテストユーティリティの作成時に参照する。

## 原則

テストが検証すべきは実際の振る舞いであり、モックの振る舞いではない。モックは隔離の手段であって、テスト対象ではない。

## アンチパターン 1: モックの振る舞いをテストしている

```typescript
// Bad: モックの存在を検証している
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});

// Good: 実コンポーネントの振る舞いを検証する
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByRole('navigation')).toBeInTheDocument();
});
```

アサーションを書く前に「これはモックの存在確認か、実際の振る舞いの確認か」を問う。モックの存在確認なら、アサーションを削除するかモックをやめる。

## アンチパターン 2: プロダクションコードにテスト専用メソッド

```python
# Bad: テストでしか使わない destroy() がプロダクションクラスにある
class Session:
    async def destroy(self):
        await self._workspace.cleanup(self.id)

# Good: テスト用のクリーンアップはテストユーティリティに置く
# test_utils.py
async def cleanup_session(session: Session):
    workspace = session.get_workspace_info()
    if workspace:
        await workspace_manager.cleanup(workspace.id)
```

メソッドを追加する前に「これはテストでしか呼ばれないか？」を問う。Yesならテストユーティリティに置く。

## アンチパターン 3: 依存関係を理解せずにモック

```python
# Bad: テストが依存する副作用をモックで消している
def test_detects_duplicate():
    with patch('catalog.discover_and_cache', return_value=None):
        add_server(config)      # 設定が書き込まれるはず
        add_server(config)      # 重複検出されるはず — だがモックで書き込みが消えている

# Good: テストが依存しない部分だけをモックする
def test_detects_duplicate():
    with patch('server_manager.start'):  # 遅い起動だけモック
        add_server(config)      # 設定書き込みは実際に行われる
        add_server(config)      # 重複検出される
```

モックする前に：
1. 実メソッドの副作用は何か？
2. このテストはその副作用に依存しているか？
3. 依存しているなら、もっと下のレイヤーでモックする

「念のためモックしておく」は危険信号。

## アンチパターン 4: 不完全なモック

```typescript
// Bad: 使うフィールドだけモック — 下流のコードが metadata を参照して壊れる
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' },
};

// Good: 実APIのレスポンス構造を完全に再現する
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' },
  metadata: { requestId: 'req-789', timestamp: 1234567890 },
};
```

モックレスポンスを作る前に、実APIのレスポンス構造を確認する。不確実なら、ドキュメントにあるフィールドをすべて含める。

## 危険信号

以下に気づいたら、モックの使い方を見直す：

- モックのセットアップがテストロジックより長い
- テストを通すためにすべてをモックしている
- モックを外すとテストが壊れる（実装ではなくモックへの依存）
- なぜモックが必要か説明できない

モックが複雑すぎるなら、実コンポーネントを使った結合テストの方がシンプルで信頼性が高いことが多い。
