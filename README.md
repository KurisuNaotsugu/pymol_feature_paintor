# pymol-env（pymol-topology）

UniProt アクセッションから **AlphaFold DB の構造ファイル**を取得し、PyMOL にロードするための小さな Python プロジェクトです。あわせて、UniProt の膜トポロジー等の feature に沿った着色や、AlphaFold 側の `uniprotSequence` と UniProt 側の配列の突合も行えます。

## できること

- `AlphaFold DB` の `prediction/{accession}` を呼び出し、モデルの **mmCIF / PDB**（対応する拡張子）URLを選択してダウンロード
- ダウンロードした構造ファイルをローカルへキャッシュ（既存ファイルは再ダウンロードしない）
- PyMOL から取得した構造を読み込み、ズーム
- UniProt の `features`（例: `TRANSMEM` / `TOPO_DOM`）から `DomainInfo` を組み立て、PyMOL で領域ごとに着色（`paint_feature`）
- 取得に使った AlphaFold のレスポンスから配列を取り出し、`UniProt` の配列と突合（一致/不一致の判定）

## 想定利用シーン

- PyMOL で AlphaFold DB の構造を素早く可視化したい
- 膜タンパクなど、UniProt のトポロジー注釈に沿って色分けしたい
- UniProt と AlphaFold の配列が食い違っていないか、軽く検証したい

## 前提条件

- Python: `>= 3.11`（`pyproject.toml` では `^3.11`）
- 通信: `requests`（依存）
- PyMOL:
  - `src/plugin/fetch_af_structure.py` は `pymol.cmd` に依存するため、**PyMOL に同梱の Python** で実行できることが前提です（通常の `venv` だけでは `from pymol import cmd` が失敗することがあります）
  - `api` / `core` / `services` などを import するには、**`src` が Python のモジュール検索パスに含まれる**必要があります。次のいずれかで満たせます。
    - **推奨（下記「推奨運用」）:** conda 環境に `PYTHONPATH` で `…/pymol_env/src` を指定する
    - **代替:** 同じ Python 環境に `poetry install` で本パッケージを入れる（`site-packages` 経由で import）
    - **代替:** ターミナルから PyMOL を起動するときだけ `export PYTHONPATH=…/src` する、またはリポジトリルートをカレントにして起動し `core.paths` 等で解決する運用

## リポジトリ構成

```
pymol_env/
├── pyproject.toml
├── README.md
├── src/
│   ├── api/                     # AlphaFold / UniProt の HTTP、ApiResponse（base.py）、pipeline（レスポンス取得）
│   ├── core/                    # models, http, cache, paths（`src` 解決）, api_response_validation
│   ├── services/                # 構造 URL 抽出・配列抽出・配列検証（alphafold_extractor 等）
│   ├── converter/               # feature 集計・DomainInfo・CSV ロード・pipeline（`domain_infos_from_response`）
│   ├── molpaint/                # Painter（`cmd.color`）。PyMOL 本体の `pymol` パッケージと名前衝突しないよう `molpaint` とする
│   └── plugin/                  # PyMOL から `run` するエントリ
│       ├── fetch_af_structure.py  # `fetch_af` を登録
│       ├── paint_feature.py       # `register_*` / `paint_feature`
│       └── plugin_test.py         # `hello_pymol`（最小サンプル）
└── tests/                       # CLI 手動テスト（ネットワーク参照）
```

`pyproject.toml` の `[tool.poetry.packages]` では `src` 直下の `api`, `core`, `services`, `converter`, `molpaint`, `plugin` をパッケージとして登録しています。CLI テスト（`tests/`）は `core.paths.ensure_project_src_on_syspath` で `src` を解決します。PyMOL プラグインは、**conda の `PYTHONPATH` または `poetry install` 済み環境**で `api` 等が import できる状態にしてください。

## インストール

依存関係は `poetry` を使って導入します。

```bash
poetry install
poetry shell
```

## 推奨運用（conda の `PYTHONPATH` と `~/.pymolrc`）

PyMOL を **conda 環境**（例: `pymol-dev`）から起動する場合の、実運用に近いセットアップです。

### 1. conda 環境に `PYTHONPATH` を指定する

リポジトリの **`src` ディレクトリの絶対パス**を、`PYTHONPATH` としてその環境に登録します。これで `from api...` などが PyMOL 内の Python から解決されます。

```bash
conda activate pymol-dev
conda env config vars set PYTHONPATH=/path/to/pymol_env/src
conda deactivate
conda activate pymol-dev
```

`/path/to/pymol_env` は自分のクローンに置き換えてください（例: macOS では `$HOME/pymol_env/src`）。

`conda activate` 時に `WARNING: overwriting environment variables set in the machine` と `overwriting variable ['PYTHONPATH']` が出ることがあります。シェル側で既に `PYTHONPATH` が設定されているとき、**環境用の値で上書きする**旨の通知です。意図どおりなら問題ありません。

**補足:** 一時的に試すだけなら、起動前に `export PYTHONPATH=/path/to/pymol_env/src` でも同じです。毎回の入力を避けるなら、上記の `conda env config vars` かシェルのエイリアスが便利です。

### 2. `~/.pymolrc` にプラグインの `run` を書いておく

PyMOL は起動時に **ホームディレクトリの `~/.pymolrc`** を読み、記述されたコマンドを実行します。毎回コンソールで `run` しなくてよいように、プラグインスクリプトの読み込みをここに書いておく運用にできます。

例（パスは環境に合わせて**絶対パス**に置き換え）:

```text
run /Users/you/pymol_env/src/plugin/fetch_af_structure.py
run /Users/you/pymol_env/src/plugin/paint_feature.py
```

読み込み後は、従来どおり `fetch_af`、`preview_feature_domains_from_accession` / `register_feature_domain_subset`、`paint_feature` などがそのセッションで利用できます。不要なプラグインは行を削除するかコメントアウトしてください（PyMOL のバージョンによっては `#` 行が使えない場合があるため、確実には該当行を削除します）。

**注意:** `.pymolrc` は PyMOL をどの経路で起動しても読み込まれるため、**上記 1 の `PYTHONPATH` が効く起動方法**（同じ conda 環境の `pymol` など）と組み合わせないと、自動 `run` 後に import エラーになることがあります。

## 使い方（PyMOL プラグイン）

`src/plugin/` 直下の `fetch_af_structure.py` / `paint_feature.py` / `plugin_test.py` は **PyMOL 上で `run` して読み込む**前提です。一般の Python だけでは `from pymol import cmd` が使えないため、ターミナルから `python src/plugin/...` と単体実行する想定ではありません（`plugin_test.py` は依存が `pymol` のみなので、環境によっては動く場合があります）。

### PyMOL 上での実行手順（GUI）

1. **conda + `PYTHONPATH` + `.pymolrc` を使う場合**  
   「推奨運用」のとおりセットしておけば、起動時に `.pymolrc` の `run` が実行され、手動で `run` する必要はありません（手動で読み直したいときだけ `run` してください）。

2. **（代替）ターミナルでリポジトリルートへ移動してから PyMOL を起動する**  
   ```bash
   cd /path/to/pymol_env
   pymol
   ```  
   カレントが `pymol_env` だと、一部のパス解決や `poetry install` 済み環境との整合が取りやすくなります。

3. **PyMOL ウィンドウ下部のコマンドライン**（または `Cmd` / Python 入力欄）を開く。

4. **手動で `run` する場合**（パスは **絶対パス**が確実です）。  
   プロジェクトルートを `$REPO` とすると次のとおりです。

   ```text
   run $REPO/src/plugin/fetch_af_structure.py
   ```

   例（macOS。`<ユーザー名>` は自分の macOS ログイン名に置き換え。`/Users/you/` のような **ダミーパスは存在しない**）:

   ```text
   run /Users/<ユーザー名>/pymol_env/src/plugin/fetch_af_structure.py
   ```

   実パスはターミナルで `echo $HOME` または `pwd`（リポジトリルートに `cd` したあと）で確認できます。

   `run` は PyMOL 組み込みの Python でファイルを実行し、`from pymol import cmd` や `cmd.extend(...)` が動きます。`api` / `molpaint` などが import できるよう、**conda の `PYTHONPATH`（推奨運用）**、または **`poetry install` 済みの同一 Python**、または **`export PYTHONPATH=…/src`** を用意してください。

5. **登録されたコマンドを実行する**（例: `fetch_af P12345`）。  
   読み込んだスクリプトごとに利用できる名前は下表のとおりです。

**メニューから読み込む場合**（バージョンにより名称が異なります）  
`File` → `Run Script...` などで `src/plugin/*.py` を指定しても読み込めます。カレントがリポジトリ外で import に失敗する場合は、**先にターミナルで `cd` してから `pymol`** するか、**`poetry install` 済み**の PyMOL 用 Python で起動してください。

### `src` のパス解決（`core.paths`）

プラグイン本体はパス解決を行いません。CLI テストと同様に、必要なら別途 `core.paths.ensure_project_src_on_syspath(anchor=__file__)` で `src` を載せる運用にできます。

1. **まず** `Path.cwd() / "src"` がプロジェクトの `src` かどうか（`api` と `services` があるか）を見る。  
   → **ターミナルから PyMOL を起動するときは、先に `cd` で `pymol_env` に移動してから `pymol`** すると確実です。
2. だめなら **`run` したスクリプトのパス**から親ディレクトリを辿り、`src` を探す。

**補足**

- 依存パッケージ（`requests` など）は、PyMOL が使う Python に `poetry install` または `pip install` で入れておくか、conda 環境に合わせて入れてください。
- **`api` を import するには** `src` が `PYTHONPATH` に含まれるか、`poetry install` でパッケージが入っている必要があります（推奨運用の conda `PYTHONPATH` を参照）。
- バッチだけ実行する場合は、**`PYTHONPATH` を付けた環境で**、または **カレントを `pymol_env` にしたうえで** `pymol -cq -d "run ...; コマンド; quit"` の形で **`run` に絶対パス**を渡します（下記「ヘッドレス実行の例」）。

| スクリプト | 読み込み後に使うコマンド（例） | 用途 |
|------------|-------------------------------|------|
| `fetch_af_structure.py` | `fetch_af P12345` | AlphaFold から構造を取得してロードし、配列検証まで行う |
| `paint_feature.py` | `preview_feature_domains_from_accession` → `register_feature_domain_subset` → `paint_feature`（下記） | UniProt の feature に沿って `DomainInfo` を登録し、着色 |
| `paint_feature.py` | `register_feature_from_csv ...` | CSV から `DomainInfo` を読み込み登録 |
| `plugin_test.py` | `hello_pymol` | `cmd.extend` の最小動作確認 |

### PyMOL での典型ワークフロー（構造取得 → feature 着色）

1. まず構造取得スクリプトを `run` し、`fetch_af` で AlphaFold 構造をロードする（オブジェクト名は `AF_<accession>`）。
2. 続けて `paint_feature.py` を `run` し、`preview_feature_domains_from_accession` で全 feature type から `DomainInfo` 候補を取得して一覧表示し、`register_feature_domain_subset` で `domain_name` / `description` に一致するものだけを登録する。
3. `paint_feature` で着色する。

```text
run $REPO/src/plugin/fetch_af_structure.py
fetch_af P12345
run $REPO/src/plugin/paint_feature.py
preview_feature_domains_from_accession P12345
register_feature_domain_subset AF_P12345, Transmembrane, Helical
paint_feature AF_P12345, AF_P12345
```

構造が未ロードのとき `paint_feature` はエラーで終了します。先に `fetch_af` などでロードしてください。

---

### AlphaFold 構造を取得してロードする

#### 1. スクリプトを読み込む

```text
run $REPO/src/plugin/fetch_af_structure.py
```

#### 2. `fetch_af` を実行

```text
fetch_af P12345
```

この `fetch_af` コマンドは内部で以下を行います。

- `P12345` を UniProt accession として扱う
- AlphaFold DB から構造（`cif` 優先 → `pdb`）
- `~/.cache/pymol_topology/alphafold/AF_{accession}.{ext}` に保存（未存在時のみ）
- `cmd.load()` で PyMOL にロードし、`cmd.zoom()` で表示を調整
- その後、AlphaFold の `uniprotSequence` と UniProt の配列を検証して結果を表示

#### （参考）ヘッドレス実行の例

`pymol` がターミナルから起動できる場合、「読み込み → `fetch_af` → 終了」を一度に行う例です。**先に `cd` でリポジトリルートに入る**と、`src` の解決が確実です。

```bash
cd /path/to/pymol_env
pymol -cq -d "run /path/to/pymol_env/src/plugin/fetch_af_structure.py; fetch_af P12345; quit"
```

`cd` のパスと `run` のパスは、自分の環境の `pymol_env` に合わせてください（両方とも同じリポジトリを指すこと）。

### feature に従って色塗り

UniProt の `features`（既定では `Transmembrane` / `Topological domain` など）から `DomainInfo` を組み立て、**一度レジストリに登録してから** PyMOL オブジェクトへ着色します。

#### 1. スクリプトを読み込む

```text
run $REPO/src/plugin/paint_feature.py
```

#### 2. UniProt から領域を登録する

登録名（`registry_name`）には、後で着色する **PyMOL オブジェクト名と同じ文字列**を使うと分かりやすいです（例: `fetch_af` のロード名 `AF_P12345`）。

まず **全 feature type** から `DomainInfo` を構築し、`domain_name` / `description` の一覧を表示します。

```text
preview_feature_domains_from_accession P12345
```

続けて、一覧に出た文字列と **完全一致** する条件で絞り込み登録します（`domain_name` のみ、`description` のみ、または両方＝AND）。いずれか一方は必須です。

```text
register_feature_domain_subset AF_P12345, Transmembrane, Helical
```

`preview_feature_domains_from_accession` の第 2 引数以降（省略可）: `chain`, `label_mode`。詳細は `src/plugin/paint_feature.py` を参照してください。

CSV から読む場合:

```text
register_feature_from_csv AF_P12345, /path/to/regions.csv
```

#### 3. 着色する

**すでに `fetch_af` などで構造がロード済み**で、オブジェクト名が `AF_P12345` のとき:

```text
paint_feature AF_P12345, AF_P12345
```

第 1 引数が登録名、第 2 引数が着色対象オブジェクト名です。対象オブジェクトが未ロードの場合はエラーになります（自動では AlphaFold を取得しません）。

### （参考）プラグイン動作確認

`cmd.extend` でコマンドを登録する最小例です。

```text
run $REPO/src/plugin/plugin_test.py
hello_pymol
```

## 使い方（コマンドライン）

リポジトリルートで、通常の Python（PyMOL 不要）から実行します。`src` は各テストスクリプトが `core.paths.ensure_project_src_on_syspath` で解決します。

**UniProt の feature 抽出 → `DomainInfo` までの確認**（ネットワーク必須）:

```bash
python tests/test_feature_extract.py P69905
```

`--feature-types` などは `python tests/test_feature_extract.py --help` を参照してください。

**AlphaFold / UniProt API と配列検証の統合確認**（ネットワーク必須）:

```bash
python tests/test_alphafold_api.py P69905
```

## プロジェクト構造（層と受け渡しデータ）

このプロジェクトは「**生レスポンス (`ApiResponse`) を API 層で受け、`converter` で用途向けデータクラスへ変換し、最後に PyMOL へ適用**」する構成です。

| 層 | 主な責務 | 主な入力 | 主な出力（データクラス/型） |
|---|---|---|---|
| `src/core` | 共通モデル・HTTP・キャッシュ・レスポンス検証 | - | `StructureArtifact` / `AminoAcidSequence` |
| `src/api` | 外部 API 呼び出し（取得のみ）。`base.py` に `ApiResponse` | `accession: str` | `ApiResponse` |
| `src/services` | API レスポンスの抽出/検証/取得オーケストレーション | `ApiResponse` など | `StructureArtifact` / `AminoAcidSequence` / `SequenceValidationResult` / `UniprotFeatures` |
| `src/converter` | feature 集計（`feature_aggregation.py`）・`DomainInfo` 構築・色付与（`ApiResponse` 起点は `converter/pipeline.py`） | `ApiResponse` / `UniprotFeatures` | `DomainInfo`（`ColorDef` 付与済み） |
| `src/molpaint/painter` | 色付与済み `DomainInfo` を検証し、PyMOL selection を組み立てて着色 | `DomainInfo`（1 件） | PyMOL への `cmd.color()` 適用（副作用） |
| `src/plugin/` | PyMOL から呼ぶエントリ (`fetch_af`, `register_*`, `paint_feature`) | コマンド引数 | 上記各層を接続して実行 |
| `tests/` | CLI 手動テスト（`test_feature_extract.py`, `test_alphafold_api.py`） | コマンド引数 | レスポンス表示・検証結果表示 |

### 主要データクラス（どこで使うか）

- `ApiResponse`（`src/api/base.py`）
  - 形: `status_code: int`, `headers: dict[str, str]`, `body: Any`, `raw_text: str`
  - 用途: `src/api` の戻り値として統一し、`src/services` が `body` を解釈
- `StructureArtifact`（`src/core/models.py`）
  - 形: `accession`, `format`, `local_path`, `source_url`, `checksum?`
  - 用途: `AlphaFoldDBFetcherClient`（`src/api/alphafold.py`）の `fetch_structure()` の成果物（PyMOL load の入力）
- `AminoAcidSequence`（`src/core/models.py`）
  - 形: `value: str`（`normalized` / `matches()` を提供）
  - 用途: AlphaFold と UniProt の配列比較に共通利用
- `SequenceValidationResult`（`src/services/sequence_validation.py`）
  - 形: `match`, `af_sequence`, `uniprot_sequence`, `message`
  - 用途: 配列一致検証の結果を UI/CLI/PyMOL 側へ返す
- `DomainInfo`（`src/converter/constractor.py`）
  - 形: `domain_name`, `spans`（複数区間可）, `chain?`, `color?`（`ColorDef`）
  - 用途: トポロジー領域の標準表現。`DomainInfoFactory` が UniProt features から生成し、`DomainColorScheme().color_fill(リスト)` で一覧に重複のない色名を付与
- `ColorDef` / `DomainColorScheme`（`src/converter/constractor.py`）
  - 形: `ColorDef` は主に PyMOL の**色名**（`name`）。`DomainColorScheme.color_fill` が `list[DomainInfo]` にパレット色を割り当て
  - 用途: 着色前に `DomainColorScheme.color_fill` でリスト単位で埋め（色名は一覧内で重複しない）、`Painter` は `ColorDef.name` をそのまま `cmd.color` に渡す

## データ形式と流れ（構造取得）

### 1) API 呼び出し

- `AlphafoldApiClient.get_prediction(accession) -> ApiResponse`
- `ApiResponse.body` は AlphaFold の JSON（`dict` または `list[dict]`）を保持

### 2) URL 抽出・形式決定

- `AlphaFoldDBClient`（`services/alphafold_extractor.py`）`pick_structure_url(resp, accession) -> tuple[url: str, fmt: str]`
- `fmt` は既定優先順 `("cif", "pdb", "bcif")`

### 3) 取得成果物へ変換

- `AlphaFoldDBFetcherClient`（`src/api/alphafold.py`）`fetch_structure(...) -> StructureArtifact`
- `StructureArtifact.local_path` は実ファイルの保存先を指す

### 4) PyMOL 適用

- `src/plugin/fetch_af_structure.py` の `fetch_af` が `cmd.load(str(artifact.local_path), ...)` を実行

キャッシュ保存先:

- ベース: `~/.cache/pymol_topology`
- サブ: `alphafold`
- ファイル名: `AF_{accession}.{cif|pdb|bcif}`

## データ形式と流れ（配列検証）

1. AlphaFold 側:
   - `ApiResponse.body` から `uniprotSequence`（または `sequence`）を抽出
   - `AminoAcidSequence` へ変換
2. UniProt 側:
   - `UniprotApiClients.get_search_response(accession) -> ApiResponse`（`fields` は付けず、必要な情報は `body` から抽出）
   - `UniprotExtractor.extract_sequence(...) -> AminoAcidSequence`
3. 比較:
   - `validate_sequence(af_sequence, uniprot_sequence) -> SequenceValidationResult`
   - `match` と `message` を PyMOL/CLI に表示

## データ形式と流れ（トポロジー着色）

**accession から進める場合**

1. `UniprotApiClients.get_search_response(accession) -> ApiResponse` で UniProt を取得し、`domain_infos_from_response(resp, accession=..., config=..., chain=...)`（`src/converter/pipeline.py`）で `list[DomainInfo]` を得る（PyMOL の `preview_feature_domains_from_accession` / `register_feature_domain_subset` はこの流れをラップしている）

**`ApiResponse` だけ渡す場合（テストや再利用向け）**

1. `domain_infos_from_response(...)`（`converter/pipeline.py`）で着色**前**の `list[DomainInfo]` を得て、必要なら呼び出し側で `DomainColorScheme().color_fill(...)`（テスト `test_feature_extract.py` も同様）

**共通の内部処理**

2. 抽出: `UniprotExtractor.extract_features(resp, accession=...) -> list[UniprotFeatures]`  
   - 各 `UniprotFeatures` は 1 件の feature について `feature`（型名）・`location`・`description` を保持する
3. 成形: `DomainInfoFactory.extract_features(list[UniprotFeatures]) -> list[DomainInfo]`  
   - 同一 `description` ごとにまとめた `DomainInfo`（`domain_name` は feature type、`description` は下位ラベル）
4. 色付与: `DomainColorScheme().color_fill(list[DomainInfo])` で未設定分に `palette`（既定は `converter.color_palette.EXTRA_PYMOL_COLOR_NAMES`）を順に割り当て（一覧内で色名が重複しない）
5. PyMOL 適用: `Painter.paint_domaininfo(cmd, object_name, domaininfo)` が `domaininfo.spans` から selection を組み立て、各 span に `cmd.color(color_name, selection)` を実行（`domaininfo` は 1 件ずつ）

## API / クラス概要（型中心）

### `src/api`（生レスポンスを返す層）

- `AlphafoldApiClient.get_prediction*() -> ApiResponse`
- `AlphaFoldDBFetcherClient.fetch_structure(...) -> StructureArtifact`（`src/api/alphafold.py`：キャッシュ・ダウンロード込み）
- `UniprotApiClients.get_search_response(...) -> ApiResponse`
- `fetch_accession_api_responses(..., include_uniprot=True, include_alphafold=True) -> AccessionApiResponses`（片方だけ取得可。Python から `from api.pipeline import fetch_accession_api_responses` として利用）

### `src/services`（用途向けの型へ変換する層）

- `AlphaFoldDBClient`（`services/alphafold_extractor.py`）`pick_structure_url` / `extract_uniprot_sequence_from_body(...) -> AminoAcidSequence | None`
- `UniprotExtractor.extract_sequence(...) -> AminoAcidSequence`
- `UniprotExtractor.extract_features(...) -> list[UniprotFeatures]`
- `validate_sequence(...) -> SequenceValidationResult`

### `src/converter`（領域仕様を作る層）

- `domain_infos_from_response(...)` → `list[DomainInfo]`（`converter/pipeline.py`）。着色は `DomainColorScheme().color_fill(...)`
- `load_domain_infos_from_csv(...)`（`converter/csv_loader.py`）
- `DomainInfoFactory.extract_features(features: list[UniprotFeatures]) -> list[DomainInfo]`（`converter/feature_aggregation.py`）
- `DomainInfo` / `ColorDef` / `DomainColorScheme`（`converter/constractor.py`）

### `src/molpaint/painter`（PyMOL 反映層）

- `Painter.paint_domaininfo(cmd, object_name, domaininfo)`  
  色付与済み `DomainInfo` を検証し、`spans` から selection を構築して `cmd.color` を実行

## よくあるトラブル

- `pymol` が import できない
  - `src/plugin/fetch_af_structure.py` は PyMOL の Python 環境が必要です（一般の Python venv では動かない可能性があります）
- `ModuleNotFoundError: No module named 'api'`（PyMOL で `run` した直後）
  - **`src` が Python のモジュール検索パスに入っていません。**「推奨運用」のとおり conda 環境に `PYTHONPATH=…/pymol_env/src` を設定するか、同じインタープリタに `poetry install` 済みか、`export PYTHONPATH=…/src` してから PyMOL を起動してください。`.pymolrc` だけ追加して `PYTHONPATH` が無い起動をしている場合も同様です。
- `ModuleNotFoundError: No module named 'molpaint'`（PyMOL で `run` した直後）
  - `src` が `sys.path` に載っていないか、古いドキュメントの `from pymol.painter` のままです。プロジェクト側のパッケージ名は PyMOL 本体の `pymol` と衝突しないよう **`molpaint`** にしています（`from molpaint.painter import Painter`）。原因と対処は上記 `api` と同じです。
- `ModuleNotFoundError: No module named 'services'`（PyMOL で `run` した直後）
  - 上記と同様に **`src` が通っていない**ことが多いです。ターミナルから起動する場合は **リポジトリルートに `cd` してから `pymol`** する、`PYTHONPATH` を付ける、または **`poetry install` 済み**の PyMOL 用 Pythonで起動してください。
- accession が空/不正
  - `RuntimeError: FetchError: ...` のようなメッセージが出ます
- API レスポンス形式が変わった場合
  - `AlphaFoldDBClient`（`services/alphafold_extractor.py` の抽出器）はメタデータから URL を探索するため、予想外の構造になると URL 抽出に失敗する場合があります

