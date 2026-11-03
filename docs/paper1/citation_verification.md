# FIQ-13: citation verification

Checked **2026-10-27**, against main `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
**Proposed bibliography; no study execution or scientific registration.**
Research support only; not investment advice.

The first twelve records match the original task-card source list. The full
40-record dossier was treated as assertions: 36 DOI records were retrieved from
Crossref's publisher-deposited registry metadata, plus four official stable
archival/proceedings records. Those are identity checks, not independent
replications of 40 papers. The dossier's 37 journal articles + one editorial +
one working paper + one conference paper classification is consistent with
these records, including review articles among the journal articles.

All bibliographic identities are established; **PBO pagination remains unresolved**.
The proposed [BibTeX](references.bib) omits that disputed field.
[Structured evidence](reference_evidence.json) records exact author names,
issue versus online versions where observed, source URLs, retrieval date and
SHA-256 of each retrieved registry response. Raw responses are session scratch,
not bundled here; their digests identify this observation, not a permanent
registry version or guaranteed future byte-for-byte response.

Status labels below refer only to bibliographic identity. VERIFIED_METADATA
uses publisher-deposited DOI fields; VERIFIED_PRIMARY/ARCHIVAL_METADATA adds a
journal/proceedings/archive record. VERIFIED_VERSION binds the cited author PDF.
Confidence is high for identity, while methodology and results remain outside
that claim. The pagination flag is a real unresolved field, not a rejected paper.
No entry's DOI, existence or citation count establishes peer-review quality or
FinanceIQ investment performance.

## Verification table (dossier numbering preserved)


| # / key | Exact authors | Issue year; title | Venue; volume(issue):pages/article | DOI / stable record | Status; correction or limit |
| --- | --- | --- | --- | --- | --- |
| 1 / `Brandt2008Surprises` | Brandt, Michael W.; Kishore, Runeet; Santa-Clara, Pedro; Venkatachalam, Mohan | 2008; Earnings Announcements are Full of Surprises | Duke University and UCLA; : pagination not established | [10.2139/ssrn.909563](https://doi.org/10.2139/ssrn.909563) | VERIFIED_VERSION. Used version: 22 January 2008 author PDF, Brandt first. SSRN DOI identifies a record initially dated 2006, with Kishore first in registry metadata; not a peer-reviewed journal article. |
| 2 / `Chen1986Economic` | Chen, Nai-Fu; Roll, Richard; Ross, Stephen A. | 1986; Economic Forces and the Stock Market | The Journal of Business; 59(3):383-403 | [10.1086/296344](https://doi.org/10.1086/296344) | VERIFIED_METADATA. Crossref records only p.383 and a January placeholder. Author institutional publication list verifies July 1986, 59(3), 383-403. |
| 3 / `Coval2007FireSales` | Coval, Joshua; Stafford, Erik | 2007; Asset fire sales (and purchases) in equity markets | Journal of Financial Economics; 86(2):479-512 | [10.1016/j.jfineco.2006.09.007](https://doi.org/10.1016/j.jfineco.2006.09.007) | VERIFIED_METADATA. Journal version 2007; do not substitute the 2005 NBER working paper. |
| 4 / `Fama1992CrossSection` | Fama, Eugene F.; French, Kenneth R. | 1992; The Cross‐Section of Expected Stock Returns | The Journal of Finance; 47(2):427-465 | [10.1111/j.1540-6261.1992.tb04398.x](https://doi.org/10.1111/j.1540-6261.1992.tb04398.x) | VERIFIED_METADATA. Journal issue June 1992. Later online ingestion date is not the issue year. Section I.A explicitly uses a conservative minimum six-month accounting gap, not a universal legal release rule. |
| 5 / `Harvey2016MultipleTesting` | Harvey, Campbell R.; Liu, Yan; Zhu, Heqing | 2016; … and the Cross-Section of Expected Returns | Review of Financial Studies; 29(1):5-68 | [10.1093/rfs/hhv059](https://doi.org/10.1093/rfs/hhv059) | VERIFIED_METADATA. Online 9 October 2015; issue January 2016. Cite the 2016 issue version. |
| 6 / `Hernan2016TargetTrial` | Hernán, Miguel A.; Robins, James M. | 2016; Using Big Data to Emulate a Target Trial When a Randomized Trial Is Not Available | American Journal of Epidemiology; 183(8):758-764 | [10.1093/aje/kwv254](https://doi.org/10.1093/aje/kwv254) | VERIFIED_METADATA. Publisher PDF title excludes the erroneous registry suffix Table 1. Method analogy only; does not identify a financial causal effect. |
| 7 / `Kapoor2023Leakage` | Kapoor, Sayash; Narayanan, Arvind | 2023; Leakage and the reproducibility crisis in machine-learning-based science | Patterns; 4(9):100804 | [10.1016/j.patter.2023.100804](https://doi.org/10.1016/j.patter.2023.100804) | VERIFIED_METADATA. Patterns article identity checked against publisher-deposited DOI metadata and archived author full text; leakage taxonomy, not a FinanceIQ effect estimate. |
| 8 / `Kolari2010EventTesting` | Kolari, James W.; Pynnönen, Seppo | 2010; Event Study Testing with Cross-sectional Correlation of Abnormal Returns | Review of Financial Studies; 23(11):3996-4025 | [10.1093/rfs/hhq072](https://doi.org/10.1093/rfs/hhq072) | VERIFIED_METADATA. Cross-sectional dependence in event studies; does not automatically validate annual IC inference. |
| 9 / `MacKinlay1997Events` | MacKinlay, A. Craig | 1997; Event Studies in Economics and Finance | Journal of Economic Literature; 35(1):13-39 | [official stable record](https://www.jstor.org/stable/2729691) | VERIFIED_ARCHIVAL_METADATA. JSTOR stable archival record. No independently established DOI added. |
| 10 / `Morck2000Information` | Morck, Randall; Yeung, Bernard; Yu, Wayne | 2000; The information content of stock markets: why do emerging markets have synchronous stock price movements? | Journal of Financial Economics; 58(1-2):215-260 | [10.1016/s0304-405x(00)00071-4](https://doi.org/10.1016/s0304-405x(00)00071-4) | VERIFIED_METADATA. Journal version 58(1-2), 215-260. Co-movement does not identify unique causal market/firm shares. |
| 11 / `Schuemie2018Calibration` | Schuemie, Martijn J.; Hripcsak, George; Ryan, Patrick B.; Madigan, David; Suchard, Marc A. | 2018; Empirical confidence interval calibration for population-level effect estimation studies in observational healthcare data | Proceedings of the National Academy of Sciences; 115(11):2571-2577 | [10.1073/pnas.1708282114](https://doi.org/10.1073/pnas.1708282114) | VERIFIED_METADATA. Archived article and PMID 29531023 match. Calibration in healthcare is an analogy requiring finance-specific assumptions. |
| 12 / `Vuolteenaho2002Returns` | Vuolteenaho, Tuomo | 2002; What Drives Firm‐Level Stock Returns? | The Journal of Finance; 57(1):233-264 | [10.1111/1540-6261.00421](https://doi.org/10.1111/1540-6261.00421) | VERIFIED_METADATA. February 2002 issue; December online date is separately recorded. VAR decomposition is not direct observation of causes. |
| 13 / `White2000RealityCheck` | White, Halbert | 2000; A Reality Check for Data Snooping | Econometrica; 68(5):1097-1126 | [10.1111/1468-0262.00152](https://doi.org/10.1111/1468-0262.00152) | VERIFIED_METADATA. DOI registry identity verified; no independent reproduction of the reality-check procedure. |
| 14 / `Hansen2005SPA` | Hansen, Peter Reinhard | 2005; A Test for Superior Predictive Ability | Journal of Business & Economic Statistics; 23(4):365-380 | [10.1198/073500105000000063](https://doi.org/10.1198/073500105000000063) | VERIFIED_METADATA. DOI registry identity verified; SPA requires a declared loss, benchmark and candidate family. |
| 15 / `Bailey2014DeflatedSharpe` | Bailey, David H.; López de Prado, Marcos | 2014; The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality | The Journal of Portfolio Management; 40(5):94-107 | [10.3905/jpm.2014.40.5.094](https://doi.org/10.3905/jpm.2014.40.5.094) | VERIFIED_METADATA. HTML italics/newlines removed from deposited title. Sharpe-specific adjustment is not an automatic correction for annual rank IC. |
| 16 / `Bailey2017PBO` | Bailey, David H.; Borwein, Jonathan M.; López de Prado, Marcos; Zhu, Qiji Jim | 2017; The probability of backtest overfitting | The Journal of Computational Finance; 20(4): pagination not established | [10.21314/jcf.2016.322](https://doi.org/10.21314/jcf.2016.322) | VERIFIED_IDENTITY_PAGINATION_UNVERIFIED. Identity, full author initials and April 2017 issue verified. Pagination UNVERIFIED: dossier says 39-70, author publication list says 39-69; registry omits pages and publisher download requires sign-in. Pages omitted rather than resolving by guess. |
| 17 / `Holm1979Sequential` | Holm, Sture | 1979; A Simple Sequentially Rejective Multiple Test Procedure | Scandinavian Journal of Statistics; 6(2):65-70 | [official stable record](https://www.jstor.org/stable/4615733) | VERIFIED_ARCHIVAL_METADATA. JSTOR issue table verifies author/title/year/6(2)/65-70. Stable URL retained; no DOI inferred from stable identifier. |
| 18 / `Benjamini1995FDR` | Benjamini, Yoav; Hochberg, Yosef | 1995; Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing | Journal of the Royal Statistical Society Series B: Statistical Methodology; 57(1):289-300 | [10.1111/j.2517-6161.1995.tb02031.x](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x) | VERIFIED_METADATA. Original 1995 issue retained; later digital publication date does not change citation year. |
| 19 / `Benjamini2001Dependency` | Benjamini, Yoav; Yekutieli, Daniel | 2001; The control of the false discovery rate in multiple testing under dependency | The Annals of Statistics; 29(4):1165-1188 | [10.1214/aos/1013699998](https://doi.org/10.1214/aos/1013699998) | VERIFIED_METADATA. DOI registry metadata checked; dependence assumptions differ from BH. |
| 20 / `Cawley2010Selection` | Cawley, Gavin C.; Talbot, Nicola L. C. | 2010; On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation | Journal of Machine Learning Research; 11(70):2079-2107 | [official stable record](https://jmlr.org/papers/v11/cawley10a.html) | VERIFIED_PRIMARY_METADATA. Official JMLR entry, 11(70), 2079-2107. No DOI invented. |
| 21 / `Bergmeir2018CV` | Bergmeir, Christoph; Hyndman, Rob J.; Koo, Bonsoo | 2018; A note on the validity of cross-validation for evaluating autoregressive time series prediction | Computational Statistics & Data Analysis; 120:70-83 | [10.1016/j.csda.2017.11.003](https://doi.org/10.1016/j.csda.2017.11.003) | VERIFIED_METADATA. 2018 issue version verified. Dossier online-2017 assertion not independently established from retrieved registry fields; not copied as verified. |
| 22 / `Petersen2009Panel` | Petersen, Mitchell A. | 2009; Estimating Standard Errors in Finance Panel Data Sets: Comparing Approaches | Review of Financial Studies; 22(1):435-480 | [10.1093/rfs/hhn053](https://doi.org/10.1093/rfs/hhn053) | VERIFIED_METADATA. Online 2008; issue 2009. Does not establish that three time clusters are sufficient. |
| 23 / `Cameron2008Bootstrap` | Cameron, A. Colin; Gelbach, Jonah B.; Miller, Douglas L. | 2008; Bootstrap-Based Improvements for Inference with Clustered Errors | Review of Economics and Statistics; 90(3):414-427 | [10.1162/rest.90.3.414](https://doi.org/10.1162/rest.90.3.414) | VERIFIED_METADATA. DOI registry bibliographic identity checked; full methods/results not independently verified. |
| 24 / `Gu2020ML` | Gu, Shihao; Kelly, Bryan; Xiu, Dacheng | 2020; Empirical Asset Pricing via Machine Learning | The Review of Financial Studies; 33(5):2223-2273 | [10.1093/rfs/hhaa009](https://doi.org/10.1093/rfs/hhaa009) | VERIFIED_METADATA. Publisher identity and sections 1.7-1.8 checked: temporal train/validation/test separation and out-of-sample evaluation. No independent result reproduction; US results do not establish a BIST edge. |
| 25 / `Drobetz2021European` | Drobetz, Wolfgang; Otto, Tizian | 2021; Empirical asset pricing via machine learning: evidence from the European stock market | Journal of Asset Management; 22(7):507-538 | [10.1057/s41260-021-00237-x](https://doi.org/10.1057/s41260-021-00237-x) | VERIFIED_METADATA. Publisher methods state a four-month assumed lag and sequential training/validation/testing. Not a BIST universal release date. |
| 26 / `McLean2016Predictability` | McLean, R. David; Pontiff, Jeffrey | 2016; Does Academic Research Destroy Stock Return Predictability? | The Journal of Finance; 71(1):5-32 | [10.1111/jofi.12365](https://doi.org/10.1111/jofi.12365) | VERIFIED_METADATA. Use 2016 issue. Academic publication/post-publication decay is distinct from financial-statement release timing; dossier early-2015 assertion not verified here. |
| 27 / `Hou2020Replication` | Hou, Kewei; Xue, Chen; Zhang, Lu | 2020; Replicating Anomalies | The Review of Financial Studies; 33(5):2019-2133 | [10.1093/rfs/hhy131](https://doi.org/10.1093/rfs/hhy131) | VERIFIED_METADATA. Online 2018; issue 2020. |
| 28 / `Jensen2023Replication` | Jensen, Theis Ingerslev; Kelly, Bryan; Pedersen, Lasse Heje | 2023; Is There a Replication Crisis in Finance? | The Journal of Finance; 78(5):2465-2518 | [10.1111/jofi.13249](https://doi.org/10.1111/jofi.13249) | VERIFIED_METADATA. Registry metadata verified; do not present all replication literature as reaching the same conclusion. |
| 29 / `Chen2022OpenSource` | Chen, Andrew Y.; Zimmermann, Tom | 2022; Open Source Cross-Sectional Asset Pricing | Critical Finance Review; 11(2):207-264 | [10.1561/104.00000112](https://doi.org/10.1561/104.00000112) | VERIFIED_METADATA. Correct DOI 10.1561/104.00000112. Author split corrected to Chen, Andrew Y., using author names on publisher-hosted appendix; appendix dated 2020 is not the 2022 journal version. |
| 30 / `Levy2026Caution` | Levy, Bradford | 2026; Caution Ahead: Numerical Reasoning and Look‐Ahead Bias in AI Models | Journal of Accounting Research; 64(3):1139-1188 | [10.1111/1475-679x.70058](https://doi.org/10.1111/1475-679x.70058) | VERIFIED_METADATA. Correct author split: Levy, Bradford. First VoR online 6 May 2026; 64(3), 1139-1188. Specific LLM experiments, not a universal claim about all models/tasks. |
| 31 / `Wolff2024StockPicking` | Wolff, Dominik; Echterling, Fabian | 2024; Stock picking with machine learning | Journal of Forecasting; 43(1):81-102 | [10.1002/for.3021](https://doi.org/10.1002/for.3021) | VERIFIED_METADATA. Online 2023; issue 2024. Publisher PDF Section 2 uses historical constituents and a three-month fundamental lag; its carry-forward/median imputation is not adopted by FinanceIQ. |
| 32 / `Brown1992Survivorship` | Brown, Stephen J.; Goetzmann, William; Ibbotson, Roger G.; Ross, Stephen A. | 1992; Survivorship Bias in Performance Studies | Review of Financial Studies; 5(4):553-580 | [10.1093/rfs/5.4.553](https://doi.org/10.1093/rfs/5.4.553) | VERIFIED_METADATA. DOI registry identity verified; survivorship mechanism cannot supply a transferable FinanceIQ bias coefficient. |
| 33 / `Shumway1997Delisting` | Shumway, Tyler | 1997; The Delisting Bias in CRSP Data | The Journal of Finance; 52(1):327-340 | [10.1111/j.1540-6261.1997.tb03818.x](https://doi.org/10.1111/j.1540-6261.1997.tb03818.x) | VERIFIED_METADATA. DOI registry identity verified; missing delisting returns are a separate measurement problem from membership coverage. |
| 34 / `David2019Leakage` | David, Zachary | 2019; Information leakage in financial machine learning research | Algorithmic Finance; 8(1-2):1-4 | [10.3233/af-190900](https://doi.org/10.3233/af-190900) | VERIFIED_METADATA. Publisher PDF explicitly Editorial; not counted as peer-reviewed original research. |
| 35 / `Sezer2020Review` | Sezer, Omer Berat; Gudelek, Mehmet Ugur; Ozbayoglu, Ahmet Murat | 2020; Financial time series forecasting with deep learning : A systematic literature review: 2005–2019 | Applied Soft Computing; 90:106181 | [10.1016/j.asoc.2020.106181](https://doi.org/10.1016/j.asoc.2020.106181) | VERIFIED_METADATA. Review article; metadata verification is not replication of its surveyed results. |
| 36 / `Miotto2016DeepPatient` | Miotto, Riccardo; Li, Li; Kidd, Brian A.; Dudley, Joel T. | 2016; Deep Patient: An Unsupervised Representation to Predict the Future of Patients from the Electronic Health Records | Scientific Reports; 6(1):26094 | [10.1038/srep26094](https://doi.org/10.1038/srep26094) | VERIFIED_METADATA. Adjacent biomedical representation method; bibliographic check only, not a proposed FinanceIQ model. |
| 37 / `Argelaguet2020MOFA` | Argelaguet, Ricard; Arnol, Damien; Bredikhin, Danila; Deloro, Yonatan; Velten, Britta; Marioni, John C.; Stegle, Oliver | 2020; MOFA+: a statistical framework for comprehensive integration of multi-modal single-cell data | Genome Biology; 21(1):111 | [10.1186/s13059-020-02015-1](https://doi.org/10.1186/s13059-020-02015-1) | VERIFIED_METADATA. Adjacent biological multi-modal method; bibliographic check only. |
| 38 / `Chernozhukov2018DML` | Chernozhukov, Victor; Chetverikov, Denis; Demirer, Mert; Duflo, Esther; Hansen, Christian; Newey, Whitney; Robins, James | 2018; Double/debiased machine learning for treatment and structural parameters | The Econometrics Journal; 21(1):C1-C68 | [10.1111/ectj.12097](https://doi.org/10.1111/ectj.12097) | VERIFIED_METADATA. Adjacent causal-estimation method; does not solve unidentified financial causality. |
| 39 / `Brodersen2015CausalImpact` | Brodersen, Kay H.; Gallusser, Fabian; Koehler, Jim; Remy, Nicolas; Scott, Steven L. | 2015; Inferring causal impact using Bayesian structural time-series models | The Annals of Applied Statistics; 9(1):247-274 | [10.1214/14-aoas788](https://doi.org/10.1214/14-aoas788) | VERIFIED_METADATA. Adjacent counterfactual time-series method; assumptions not validated for FinanceIQ. |
| 40 / `Melnychuk2022CausalTransformer` | Melnychuk, Valentyn; Frauen, Dennis; Feuerriegel, Stefan | 2022; Causal Transformer for Estimating Counterfactual Outcomes | Proceedings of the 39th International Conference on Machine Learning; 162:15293-15329 | [official stable record](https://proceedings.mlr.press/v162/melnychuk22a.html) | VERIFIED_PRIMARY_METADATA. Official ICML 2022/PMLR conference entry and BibTeX. No arXiv DOI substituted for a proceedings DOI. |

## Version/type corrections and direct evidence

- **Brandt et al.**: [author PDF, first page](https://www.anderson.ucla.edu/documents/areas/fac/finance/santa_clara_surprises.pdf)
  states 22 January 2008 and Brandt, Kishore, Santa-Clara, Venkatachalam.
  SSRN DOI metadata starts with Kishore and dates the initial record 2006.
  Cite the used 2008 working-paper version, never a peer-reviewed journal version.
- **Chen-Roll-Ross**: [Roll's institutional publication list](https://www.anderson.ucla.edu/faculty-and-research/finance/faculty/roll)
  verifies July 1986 and 383-403 where Crossref only gives 383 and January.
- **Hernán-Robins**: the [publisher PDF](https://academic.oup.com/aje/article-pdf/183/8/758/6652570/kwv254.pdf)
  excludes the registry's spurious “Table 1.” suffix from the title.
- **MacKinlay and Holm**: [JSTOR article](https://www.jstor.org/stable/2729691?initiator=recommender)
  and [Holm's issue contents](https://www.jstor.org/stable/i412579) establish
  stable identities. No guessed DOI is added.
- **PBO**: [publisher issue](https://www.risk.net/ja/node/4278011) verifies
  April 2017, 20(4), versus registry online 2016. But the
  [author list](https://www.davidhbailey.com/dhbpapers/) says **39-69**, whereas
  the dossier says **39-70**. Publisher public text/registry did not resolve
  pages; the linked download required sign-in. Identity verified, pages UNKNOWN.
- **Chen-Zimmermann**: registry DOI is 10.1561/104.00000112. The
  [publisher-hosted author appendix](https://nowpublishers.com/article/details/supplementary-info/104.00000112_app.pdf)
  confirms Andrew Y. Chen, not the registry split “Andrew / Y. Chen”. Its 2020
  appendix date does not replace the 2022 journal issue year.
- **Levy**: [publisher record](https://onlinelibrary.wiley.com/doi/10.1111/1475-679x.70058)
  verifies Bradford Levy, VoR online 6 May 2026, 64(3), 1139-1188. Normalize
  the registry's single family-name field “BRADFORD LEVY”.
- **David**: [publisher PDF](https://journals.sagepub.com/doi/pdf/10.3233/AF-190900?download=true)
  explicitly says Editorial. **Melnychuk et al.**: [PMLR](https://proceedings.mlr.press/v162/melnychuk22a.html)
  is an ICML conference record, not a journal article or an arXiv DOI.

## Five post-2015 peer-reviewed additions and their bounded role

| Work | Contribution relevant to Paper 1 | Evidence and transfer limit |
| --- | --- | --- |
| Bailey et al. (2017), PBO | Models the risk of selecting a backtest winner that underperforms out of sample. | [Publisher abstract](https://www.risk.net/journal-of-computational-finance/2471206/the-probability-of-backtest-overfitting); cannot repair timing leakage or an incomplete universe; pagination unresolved. |
| Gu-Kelly-Xiu (2020) | A financial ML out-of-sample evaluation reference. | [Publisher §1.7-1.8](https://academic.oup.com/rfs/article/33/5/2223/5758276); temporal train/validation/test separation checked, results not reproduced; no BIST edge implied. |
| Drobetz-Otto (2021) | Makes an assumed four-month accounting lag and sequential training/validation/test separation explicit. | [Publisher, Data and Methods](https://link.springer.com/article/10.1057/s41260-021-00237-x); assumed lag is not a universal BIST publication date. |
| Wolff-Echterling (2024) | Uses historical S&P 500 constituents and a three-month fundamental lag. | [Publisher PDF §2-3](https://onlinelibrary.wiley.com/doi/pdf/10.1002/for.3021); its carry-forward/median imputation is not adopted. |
| Levy (2026) | Direct accounting/finance LLM experiments examine numerical reasoning and look-ahead artifacts. | [Publisher abstract and version](https://onlinelibrary.wiley.com/doi/10.1111/1475-679x.70058); model/task-specific evidence, not proof about every LLM. |

Kapoor-Narayanan supplies a broader leakage taxonomy; David is a directly useful
finance editorial but does not fill a peer-reviewed-original-research quota.
Brown and Shumway distinguish survivor conditioning from missing exit-return
measurement; neither gives a portable FinanceIQ adjustment factor.

## Multiple testing and positioning

White (2000), Hansen (2005), Harvey-Liu-Zhu (2016), and Bailey-López de Prado
(2014) are included with verified DOI metadata. Holm, BH and BY are included
with separate familywise/FDR roles. Citation inclusion does not adopt a test or
establish valid base p-values, a complete trial family or appropriate dependence
handling. Deflated Sharpe is not an automatic correction for annual Spearman IC.

[Fama-French §I.A](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1992.tb04398.x)
already uses a conservative minimum six-month gap for accounting information.
Paper 1 should present an auditable case application and correction, not claim
invention of the PIT principle. Existing old/new evaluations change several
things together; their difference is not an isolated causal timing effect.
Hernán-Robins/Schuemie are methodological analogies, not financial causal proof.
Adjacent methods 36-40 are metadata-checked context, not program/model decisions.

## Dossier/OpenAlex claims that are not independently established

The supplied 14-page PDF was read in full; its identity is recorded in the JSON.
Its named auxiliary bibliography, verification table, query JSON and hash
manifest were not supplied with that PDF in the referenced chat attachment.
No OpenAlex IDs or raw responses are included there for independent inspection.
Accordingly the assertions “40 OpenAlex matches”, “eight queries” and “200
first-page results retained” remain **REPORTED / UNVERIFIED**, not a reproduced
search. No Scopus, institutional access or comprehensive systematic-review claim
is made. Registry agreement and OpenAlex agreement would not be two independent
method validations in any case.

Next: use the verified subset in FIQ-15 with its existing-result-only boundary;
resolve PBO pagination before submission. Do not use the dossier's verification
labels to upgrade methods/results, unseen attachments or protected data.
