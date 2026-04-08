# (pymol plugin) pymol_feature_paintor

## プロジェクト概要

　本プロジェクトはオープンソースの分子構造グラフィクツールであるpymolのプラグインとして開発され、pymol上に表示されているタンパク質3Dモデルに対して、指定領域ごとの着色を施す機能を付与します。また、領域指定はcsvファイルによる指定およびUniprot APIから取得した feature 情報から指定することが可能です。3D構造データは AlphaFold DB から uniprotアクセッション番号をキーとして自動的にロードすることも可能です。

## 主な機能

### 1. 3D構造データのロード (Alphahold DB API)

- Alphahold DB API () からuniprot開くセッション番号をキーにして構造データ取得
- pymol上に描画する

### 2. 指定領域の着色

- 指定したフォーマットのCSVファイルの情報に従って、構造データの指定領域を着色
- Uniprotアクセッション番号をキーに Uniprot から feature 情報 (二次構造情報やドメイン情報) を取得
- 指定した feature 情報の領域情報に従って構造データの指定領域を着色

### 3.  補助機能

- Alphafold DB API および Uniprot から取得した feature 情報に含まれれるアミノ酸配列の整合確認機能 (配列不一致による領域指定のズレ防止)
- 登録した feature 情報には固有の色が与えられて描写される (auto color fill)

## 想定用途

- PyMOL で AlphaFold DB の構造を素早く可視化したい
- 膜貫通領域や細胞外ドメインなどのトポロジー情報を可視化したい
- ドメインスワップなどを実施した領域を視覚的に把握したい

## セットアップ

### 1. 実行環境

　適当なパッケージ管理ツールおよび仮想環境管理ツールを使用して、オープンソース版のpymolが実行できる仮想環境を構築してください。環境構築に特段のこだわりがない場合にはconda環境での構築が最も簡単です。

- Python: `>= 3.11`

### 2. PYTHONPATHの設定

　リポジトリの `src` **ディレクトリの絶対パス**を、`PYTHONPATH` としてその環境に登録します。これで `from api...` などが PyMOL 内の Python から解決されます。

```bash
conda activate env_name
conda env config vars set PYTHONPATH=/path/to/pymol_env/src
conda deactivate
conda activate env_name
```

`/path/to/pymol_env` は自分のクローンに置き換えてください（例: macOS では `$HOME/pymol_env/src`）。

**補足:** 一時的に試すだけなら、起動前に `export PYTHONPATH=/path/to/pymol_env/src` でも同じです。毎回の入力を避けるなら、上記の `conda env config vars` かシェルのエイリアスが便利です。

### 3. .pymolrcのセットアップ

　PyMOL は起動時に **ホームディレクトリの** `~/.pymolrc` を読み、記述されたコマンドを実行します。ホームディレクトリに下記を記述した `.pymolrc` を設置することで、毎回プラグインで使用するコマンドの登録作業を省略することができます。

 

例（パスは環境に合わせて**絶対パス**に置き換え）:

```text
run /Users/you/pymol_env/src/plugin/fetch_af_structure.py
run /Users/you/pymol_env/src/plugin/paint_feature.py
```



※ `.pymolrc` を設置しない場合は、上記コマンドを毎回pymolコンソール上に入力して実行してください

**※** `.pymolrc` は**上記の** `PYTHONPATH` **の追加後に実施してください**

## リポジトリ構成

```
pymol_env/
├── pyproject.toml
├── README.md
├── src/
│   ├── api/                     # AlphaFold / UniProt の APIを直接叩く層
│   ├── core/                    # models, http, cache, api_response_validation など
│   ├── services/                # APIを叩いて取得したresponseをパースして情報を抽出する層
│   ├── converter/               # servise層で抽出したデータをさらに集計して、molpaintで使用するデータクラスへ変換する層
│   ├── molpaint/                # pymolへのfeature情報の登録や構造取得、着色を実行するためのコマンド群
│   └── plugin/                  # PyMOL から `run` するエントリ
│       ├── fetch_af_structure.py  # `fetch_af` を登録
│       ├── paint_feature.py       # `register_*` / `paint_feature`
│       └── plugin_test.py         # `hello_pymol`（プラグインテスト用）
└── tests/                       # CLI 手動テスト（ネットワーク参照）
```

`pyproject.toml` の `[tool.poetry.packages]` では `src` 直下の `api`, `core`, `services`, `converter`, `molpaint`, `plugin` をパッケージとして登録しています。

## 使い方

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
   例（macOS。`<ユーザー名>` は自分の macOS ログイン名に置き換え。`/Users/you/` のような **ダミーパスは存在しない**）:
   実パスはターミナルで `echo $HOME` または `pwd`（リポジトリルートに `cd` したあと）で確認できます。
   `run` は PyMOL 組み込みの Python でファイルを実行し、`from pymol import cmd` や `cmd.extend(...)` が動きます。`api` / `molpaint` などが import できるよう、**conda の `PYTHONPATH`（推奨運用）**、または `**poetry install` 済みの同一 Python**、または `**export PYTHONPATH=…/src`** を用意してください。
5. **登録されたコマンドを実行する**（例: `fetch_af P12345`）。
  読み込んだスクリプトごとに利用できる名前は下表のとおりです。

**メニューから読み込む場合**（バージョンにより名称が異なります）  
`File` → `Run Script...` などで `src/plugin/*.py` を指定しても読み込めます。カレントがリポジトリ外で import に失敗する場合は、**先にターミナルで `cd` してから `pymol`** するか、`**poetry install` 済み**の PyMOL 用 Python で起動してください。




| スクリプト                   | 読み込み後に使うコマンド（例）                                                                                   | 用途                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `fetch_af_structure.py` | `fetch_af P12345`                                                                                 | AlphaFold から構造を取得してロードし、配列検証まで行う            |
| `paint_feature.py`      | `preview_feature_domains_from_accession` → `register_feature_domain_subset` → `paint_feature`（下記） | UniProt の feature に沿って `DomainInfo` を登録し、着色 |
| `paint_feature.py`      | `register_feature_from_csv ...`                                                                   | CSV から `DomainInfo` を読み込み登録                 |
| `plugin_test.py`        | `hello_pymol`                                                                                     | `cmd.extend` の最小動作確認                        |


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


| 層                      | 主な責務                                                                                                | 主な入力                              | 主な出力（データクラス/型）                                                                             |
| ---------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------ |
| `src/core`             | 共通モデル・HTTP・キャッシュ・レスポンス検証                                                                            | -                                 | `StructureArtifact` / `AminoAcidSequence`                                                  |
| `src/api`              | 外部 API 呼び出し（取得のみ）。`base.py` に `ApiResponse`                                                         | `accession: str`                  | `ApiResponse`                                                                              |
| `src/services`         | API レスポンスの抽出/検証/取得オーケストレーション                                                                        | `ApiResponse` など                  | `StructureArtifact` / `AminoAcidSequence` / `SequenceValidationResult` / `UniprotFeatures` |
| `src/converter`        | feature 集計（`feature_aggregation.py`）・`DomainInfo` 構築・色付与（`ApiResponse` 起点は `converter/pipeline.py`） | `ApiResponse` / `UniprotFeatures` | `DomainInfo`（`ColorDef` 付与済み）                                                              |
| `src/molpaint/painter` | 色付与済み `DomainInfo` を検証し、PyMOL selection を組み立てて着色                                                    | `DomainInfo`（1 件）                 | PyMOL への `cmd.color()` 適用（副作用）                                                             |
| `src/plugin/`          | PyMOL から呼ぶエントリ (`fetch_af`, `register_`*, `paint_feature`)                                          | コマンド引数                            | 上記各層を接続して実行                                                                                |
| `tests/`               | CLI 手動テスト（`test_feature_extract.py`, `test_alphafold_api.py`）                                       | コマンド引数                            | レスポンス表示・検証結果表示                                                                             |


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

`**ApiResponse` だけ渡す場合（テストや再利用向け）**

1. `domain_infos_from_response(...)`（`converter/pipeline.py`）で着色**前**の `list[DomainInfo]` を得て、必要なら呼び出し側で `DomainColorScheme().color_fill(...)`（テスト `test_feature_extract.py` も同様）

**共通の内部処理**

1. 抽出: `UniprotExtractor.extract_features(resp, accession=...) -> list[UniprotFeatures]`
  - 各 `UniprotFeatures` は 1 件の feature について `feature`（型名）・`location`・`description` を保持する
2. 成形: `DomainInfoFactory.extract_features(list[UniprotFeatures]) -> list[DomainInfo]`
  - 同一 `description` ごとにまとめた `DomainInfo`（`domain_name` は feature type、`description` は下位ラベル）
3. 色付与: `DomainColorScheme().color_fill(list[DomainInfo])` で未設定分に `palette`（既定は `converter.color_palette.EXTRA_PYMOL_COLOR_NAMES`）を順に割り当て（一覧内で色名が重複しない）
4. PyMOL 適用: `Painter.paint_domaininfo(cmd, object_name, domaininfo)` が `domaininfo.spans` から selection を組み立て、各 span に `cmd.color(color_name, selection)` を実行（`domaininfo` は 1 件ずつ）

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

