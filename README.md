# Gaussian Input Preparation Tool (GUI)

- [Gaussian Input Preparation Tool (GUI)](#gaussian-input-preparation-tool-gui)
	- [1. はじめに](#1-はじめに)
		- [1.1. 概要](#11-概要)
		- [1.2. 更新履歴](#12-更新履歴)
			- [2024/9/11](#2024911)
			- [2023/12/12](#20231212)
			- [2023/11/10](#20231110)
			- [2022/10/26](#20221026)
			- [2022/10/25](#20221025)
			- [2022/10/20](#20221020)
			- [2021/6/4](#202164)
			- [2021/1/1](#202111)
			- [2020/12/31](#20201231)
	- [2. 動作条件と起動](#2-動作条件と起動)
		- [2.1. 動作確認環境](#21-動作確認環境)
		- [2.2. 起動](#22-起動)
	- [3. 使い方](#3-使い方)
		- [3.1. 構造ファイルの指定](#31-構造ファイルの指定)
		- [3.2. 出力ファイルとタイトル行の指定](#32-出力ファイルとタイトル行の指定)
		- [3.3. Link0セクションの指定](#33-link0セクションの指定)
		- [3.4. 計算レベル (Model Chemistry) の指定](#34-計算レベル-model-chemistry-の指定)
		- [3.5. ジョブの指定と出力](#35-ジョブの指定と出力)
		- [3.6. 計算条件の保存と読み込み](#36-計算条件の保存と読み込み)
	- [4. 基底系](#4-基底系)
		- [4.1. 基底系の追加](#41-基底系の追加)
	- [5. 単点計算および振動計算 (SP/Freq)](#5-単点計算および振動計算-spfreq)
	- [6. 構造最適化 (Opt/TS)](#6-構造最適化-optts)
	- [7. IRC](#7-irc)
	- [8. WFX](#8-wfx)
	- [9. NBO](#9-nbo)
	- [10. ANY](#10-any)
	- [11. バッチモード](#11-バッチモード)
	- [12. シリーズモード](#12-シリーズモード)
	- [13. Empirical Dispersion（D3/D3BJ）のパラメータの設定](#13-empirical-dispersiond3d3bjのパラメータの設定)
	- [14. Open-Shell Singlet計算用の設定](#14-open-shell-singlet計算用の設定)
	- [15. Log](#15-log)

## 1. はじめに

### 1.1. 概要

有機低分子や錯体計算に関するGaussianの典型的なジョブファイルを作成するためのツールです。構造を既存のGaussian Job File (GJF) 、XYZファイル、Gaussianのログファイルから読み込み、計算条件等を指定したファイルを出力します。単点、振動、構造最適化、遷移状態最適化、IRC計算に対応しています。また外部基底ファイルから、自動的にGen/ECPセクションを作成できます。

### 1.2. 更新履歴

#### 2024/9/11
- リファクタリングとファイル構造の整理。
- xyzファイルをsingle jobのインプットとして読むとき、最後の構造を利用するように変更。

#### 2023/12/12
- FREQ計算時にnoramanオプションをつけるようにしました。計算コストがちょっと（10%くらい？）下がります。
- stable=opt選択時に、Uにならない場合があるのを修正。

#### 2023/11/10
- dispersion (D3,D3BJ)について、Gaussianに入ってないパラメータを設定する機能（ext. param.）を追加。
- open-shell singlet計算用にguess=mixを追加。
- open-shell singlet計算用にstable=optによる単点計算と複合ジョブによる構造最適化・IRC計算に対応。
- 汎関数等の前に、開殻系の計算やstable=optを入れたジョブのときは、Uをつけるようにしました。

#### 2022/10/26
- Seriesモード（複数構造を含むxyzから一挙にジョブを作成）を追加
- Opt=modredundantを利用できるようにした。
- ファイルや文字列操作周りの大幅なりファクタリング

#### 2022/10/25
- 波動関数ファイル (WFX) 出力用、NBO計算用、任意のジョブのファイル出力機能を追加
- 細かい出力の調整とリファクタリング

#### 2022/10/20
- IRCのアルゴリズムの指定を追加。LQAの場合はrecorrect=neverが自動的に追加され、maxcycとFC/correctorの指定は無視されます。荒くはなりますが速くコケにくくなります（パスの繋がりを見るだけのとき用）。
- nosymmで計算したログファイルからも、最終構造を読み込めるように修正。

#### 2021/6/4
- EmpiricalDispersionの項目を追加（忘れていました）
- 設定によっては Optのオプションの最後に不要の , が入る場合があったのを修正。

#### 2021/1/1
- バッチモードを実装。

#### 2020/12/31
- とりあえず形にしました。

## 2. 動作条件と起動

### 2.1. 動作確認環境
- Windows 10
- Python 3.7
- wxpython 4.1.1

### 2.2. 起動
gauprep.pyw を実行してください。初期の設定は前回終了時のものとなります。

## 3. 使い方

### 3.1. 構造ファイルの指定

 - General Settings の structure fileのボタンを押してファイルを選択するか、ファイルをドラッグアンドドロップしてください。後者推奨です。
 - ファイル形式は拡張子で判別されます。gjf, com, gjc はGaussian Job File、log, out はログファイル、それ以外はXYZ形式で読み込みます。

### 3.2. 出力ファイルとタイトル行の指定

- 入力ファイルを入れると自動的に設定されますが、適宜書き直してください。出力先は構造ファイルと同じディレクトリになります。
- タイトルや出力ファイル名の ${NAME} は元の構造ファイルの拡張子以外の部分になります。例えば元ファイルが、 /hoge/fuga/input.xyz  なら input となります。
- タイトルの ${GEN} は、基底の指定が Gen となる場合にその詳細に置換されます。これは特に外部基底ファイルから読んだ場合に、後でどの基底系かわからなくならないためです。 Gen でない場合は、空欄に置換されます。

### 3.3. Link0セクションの指定

- 利用するコア数とメモリを指定してください。
- チェックポイントファイル名は自動的に出力ファイル名.chk になります。

### 3.4. 計算レベル (Model Chemistry) の指定

- 計算条件（DFT汎関数 or HF or MP2）と基底系、溶媒の扱いを入力してください。
- basis set with ECP は Rb以降 (4d金属の列以降) に適用する基底系です。通常これより重い元素にはECPの基底系を利用します。
- applied to 3d rows にチェックを入れると、K-Kr (3d金属の列) にもこちらの基底が適用されます。ただしdef2~基底系はこの周期の原子は全電子基底でECPではありません。
- 基底系の追加や扱いは後ろで詳しく述べます。
- Solvaion が none の場合、solventの指定は無視されます。

### 3.5. ジョブの指定と出力

- Job Settings のタブから出力したいものを選び、オプションを入力して、outputボタンを押してください。エラーがなければファイルが出力されます。
- 出力ファイルが存在する場合は、上書き確認されます。

### 3.6. 計算条件の保存と読み込み

- メニューバーから file > save とすると、General Settingsの部分以外の状態をファイルで保存されます。拡張子はssetとなります。
- 保存したファイルは、file > load で読み込むか、ドラッグアンドドロップで読み込むことができます（拡張子がssetである必要があります）。

## 4. 基底系

### 4.1. 基底系の追加

- 基底系は、settings 内の basis.dat および basis_h_ecp.dat に保存されていて、起動時に読み込まれます。これらを編集すれば基底系を追加することができます。Gaussian組み込みの基底系なら、これだけでOKですが、basis_h_ecp.dat (重原子用ECP基底) の方は必ずECPを持つ基底を指定する必要があります。
- Gaussian にない基底系を使う場合、Basis Set Exchange からGaussian形式でダウンロードして、基底名.gbs という名前で extbasis 内に置き、その名前をbasis.dat や basis_h_ecp.dat に書いておく必要があります。
- 作成するgbsファイルは、全ての原子の基底やECP定義を含んでいてよいです。構造に含まれる原子の情報だけが読み込まれて、出力ファイルの構造部分の下に書き込まれます。
- 作成する gbs ファイルは、基本的にBasis Set Exchangeの出力そのままでよいです。コメント行の後ろに、基底の定義、空行、ECPの定義と並んでいる必要があります。先頭部分以外に余分な空行があってはいけません。
- gbs ファイル内に必要な基底が見つからない場合はエラーとなりますが、
ECP定義が見つからない場合は、ECP部分なしでファイルの出力ができてしまうので注意してください。
- Gaussianに組み込みの基底でも、gbsファイルが存在する場合には gbsファイルが優先されます。
- gbsファイルから読み出す場合は、重原子にECPなしの全電子基底を指定することもできますが、相対論効果の扱いがうまくないGaussianで、重原子に全電子基底を適用する意味はほぼないと思います。

## 5. 単点計算および振動計算 (SP/Freq)

- run freq のチェックを外すと、単点計算 (SP) になります。
- run freq にチェックを入れると、振動計算 (FREQ) になります。

## 6. 構造最適化 (Opt/TS)

- job type から、構造最適化 (Opt)、構造最適化+振動計算 (Opt+Freq)、遷移状態構造最適化 (TS; Opt=Ts+FREQ) を選択します。
- オプションは空にすると、指定なしとなります (Gaussianのデフォルトが適用されます)。
- algorithm は、自由度が大きくてふらふらする系には GDIIS を指定すると良いことがあります。
- convergence は通常は tight 程度がよいです。低レベルでの前最適化などでは、loose にすると多少早いと思います。
- max cycle (構造最適化の最大ステップ数)は、とりあえず20-30程度で様子を見ましょう。振動するときはそのまま伸ばしても時間の無駄なことが多いです。
- max step は1ステップで動かす大きさです。これを小さくすると、より細かく動きます。ふらふらしていて微妙に収束しないときや、PESが平坦で変に大きく動いてしまうときは小さくしましょう (Gaussianのデフォルトは30で、最小値は1)。
- FC/cycle は構造最適化の際に、二次微分 (力の定数、Hessian)を計算する指定です。0 で最初だけ計算 (calcfc)、1 で毎回計算 (calcall)、N (>1) だとN回毎に計算します (calcfc + recalcfc=N)。
- modredundantに所定の書式で条件を書いておくと、opt=modredudantによる構造の固定やスキャン用のジョブを作成できます。TSの場合はここは無視されます。


## 7. IRC

- algorithmで計算方法を指定できます。通常のDFTなどでGaussianのデフォルトはHPCです。一方でLQAは（多分）GRRMの実装に近いやり方で、経路は荒くなりますがコケにくくちゃんと進みやすいです。TSから基底状態のざっくりした接続を確認する目的ではこちらのほうがよいでしょう。HPCの場合、パスをスムーズにするために1ステップ進むごとに最適化が入り、それが収束しないとそこで計算が打ち切られてしまいます。
- direction で IRC計算をする方向を指定します。
- それ以外のオプションは空欄の場合は指定なし (Gaussianのデフォルト) となります。
- maxpoints は、それぞれの方向に何点進むかの指定です (デフォルトは10)。
- stepsizeは、1点でどれだけ構造を動かすかの指定です (デフォルトは10)。
- max cycle (opt) は、それぞれの点での構造最適化の最大ステップ数です (デフォルトは20)。
- FC/predictor, FC/corrector は IRC計算のpredictor step と corrector stepで何回毎に二次微分を計算するかのオプションです。predictorで大きく動かして、correctorで修正する感じのアルゴリズムなので、IRCがコケるときはとりあえずpredictorに入れるといいかもしれません。

## 8. WFX

- 単点計算を実行して、同ファイル名のWFXファイルを出力するジョブファイルを作成します。
- density=current, pop=no (singlet) または pop=noabキーワードが利用されます。

## 9. NBO

- NBO計算用ジョブを出力します。
- Gaussianを選ぶとGaussian内蔵のNBO3.1用のジョブになり、ほかは外部NBOプログラムへのインターフェースが利用されます。
- keywordsは、通常はBNDIDXとNBOSUMだけで十分です。3CBONDやRESONANCEは特殊な分子向けです。
- 軌道の可視化が必要なときはsave in chkにチェックを入れるとsavenbosオプションが入ります。

## 10. ANY

- その他の任意ジョブ作成用です。
- テキストで入力した内容がそのままルートセクションに反映されます。
- 計算条件は左で指定したものが利用されるので、ジョブタイプに該当するキーワードなどを入れてください。
- 空欄のままにすると特にジョブタイプの指定されないファイルが出力されます（そのまま実行するとSPになります）。

## 11. バッチモード

- General Settingsのところからバッチモードに切り替えられます。
- 元となる構造ファイルをドラッグアンドドロップして入力欄に追加してください。その後シングルモードと同じようにJobのところからoutputボタンを押すと、追加した全ファイルに対して適用されてファイルが出力されます。
- ディレクトリを追加すると、そのサブディレクトリ含めて中身が全て追加されます。拡張子がssetのファイル以外は全て追加されるので注意してください。
- 出力ファイル名は、元のファイル名と同じディレクトリに、指定した形式で出力されます。${NAME} は 例えば元ファイルが、 /hoge/fuga/input.xyz  なら input となります。
- タイトル行も全て同一になりますが、${FILENAME} や ${GEN} の部分はそれぞれのファイル内容が反映されます。
- overwrite チェックを外すといちいち上書き確認のメッセージボックスがでなくなりますが、ディレクトリなどを追加する場合は思わぬ上書きが発生し得るので注意してください。

## 12. シリーズモード

- インプットとして複数構造を含むxyzファイルを読み込み、それぞれの構造に対するジョブを一挙に作成できます。
- 電荷・多重度の指定は同一になります。
- 出力ファイル名の${NUMBER}の部分は、xyzファイルの格納順になります（1～）。


## 13. Empirical Dispersion（D3/D3BJ）のパラメータの設定

- settings/B3ZERO.dat および settings/D3BJ.dat に汎関数の名前と各パラメータ値を入れておきます。
- methodにその基底関数系を選び、ext. param.をチェックすると、そのパラメータがiopで追加されます。
- 主にGaussianにパラメータが実装されていない関数系への対応に利用します（OPBEなど）。

## 14. Open-Shell Singlet計算用の設定

- stable=opt のチェックと入れると、stable=optキーワードが追加され、波動関数の安定性の確認と再計算が行えます。guess=mixと合わせると、open-shell singlet波動関数の計算に利用できます。
- Opt/TSやIRC計算の場合、stable=optの計算の後、その波動関数を読み込んで構造最適化等をおこなう複合ジョブを作成します。これによりopen-shell singletの構造最適化等ができます。

## 15. Log

- 出力等のログやエラーが発生したときにそのメッセージがここに表示されます。



