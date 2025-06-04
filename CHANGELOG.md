# Changelog

## [0.14.0](https://github.com/complytime/trestle-bot/compare/v0.13.0...v0.14.0) (2025-06-04)


### Features

* CPLYTM-754 Implement sync-oscal-content catalog command ([1f4bd88](https://github.com/complytime/trestle-bot/commit/1f4bd881c1015cf7c7cbff362b1efeb5f75cb68f))


### Bug Fixes

* CPLYTM-798 Add numerical suffix to component definition "Parameter" props ([c4e8778](https://github.com/complytime/trestle-bot/commit/c4e8778194b958c174bb45650a7c61544b43e488))


### Maintenance

* add tests ([7cb3d28](https://github.com/complytime/trestle-bot/commit/7cb3d287581e1388025fe01e235f0e26f39955b8))
* add tests ([5ee1af4](https://github.com/complytime/trestle-bot/commit/5ee1af4c078e25223638366d40c4f4d6bd77434e))
* address the kics warning for leakage ([2d41068](https://github.com/complytime/trestle-bot/commit/2d410687d836b67d5728b49577b840a4bcc8569e))
* fix lint issues ([2ae8772](https://github.com/complytime/trestle-bot/commit/2ae87729f46d21a261f325d017c4a440726bea07))
* remove unnecessary persmissions ([b2df986](https://github.com/complytime/trestle-bot/commit/b2df98659359d923d5025e78446687146353993a))
* update the ocp4 control name ([6c95b78](https://github.com/complytime/trestle-bot/commit/6c95b78310d2088063c052726a934742ca4b5759))
* update the ocp4 control name ([45da6ee](https://github.com/complytime/trestle-bot/commit/45da6eeb83fc495406012c53856236757ad63c97))

## [0.13.0](https://github.com/complytime/trestle-bot/compare/v0.12.0...v0.13.0) (2025-05-22)


### Features

* [CPLYTM-627] get mapping of profile and available control ([44828b5](https://github.com/complytime/trestle-bot/commit/44828b5bd8994c7d967991e8d9a91a4ce8c4bddd))
* Add comment to corresponding control when find missing rule ([4aef7f0](https://github.com/complytime/trestle-bot/commit/4aef7f0f4a6e5e66d5b046983d376c3bbdd1f2f5))
* add the function to get mapping of profile and available control ([7130541](https://github.com/complytime/trestle-bot/commit/71305410b2c9450511c77d2dbda3298b1d14dc7f))
* CPLYTM-656 CPLYTM-655 Create non-exist variables value in cac side when sync OSCAL CD ([34345f9](https://github.com/complytime/trestle-bot/commit/34345f9455db05583ea0aaf13500d8a079775a7e))
* CPLYTM-661, CPLYTM-662 sync OSCAL control status to cac control status ([8ae7701](https://github.com/complytime/trestle-bot/commit/8ae7701366fdc3a48943179ba5a7997d907ad646))
* CPLYTM-663 add cmd for sync OSCAL profile information to cac content ([006fba1](https://github.com/complytime/trestle-bot/commit/006fba1b8aaeab710df959e737a7dbaf867c9838))
* CPLYTM-665 CPLYTM-664 Implementation for sync-oscal-content profile command ([095b9a1](https://github.com/complytime/trestle-bot/commit/095b9a126a3a1dc558c520940ba1c3dab8a222af))
* CPLYTM-711 CPLYTM-712 Sync OSCAL component definition statements to CaC notes ([9e662f9](https://github.com/complytime/trestle-bot/commit/9e662f9e5403bbc2962c0446d71f3f4c95759025))
* CPLYTM-753 Introduce catalog subcommand for sync-oscal-content ([70e0a24](https://github.com/complytime/trestle-bot/commit/70e0a24b16d546d0b2798a66258de3a08ac68bee))
* Implemented validate and sync rule function for sync-oscal-content command ([cb7ffa0](https://github.com/complytime/trestle-bot/commit/cb7ffa05ccbb1027f2a4cc8035f2ceebb4ab8199))
* profile path resolved from cac profile name ([6b826ce](https://github.com/complytime/trestle-bot/commit/6b826ce6673d6cfe80c19d23e24c9669c182ec4b))
* updating debug logs for path reference ([685683f](https://github.com/complytime/trestle-bot/commit/685683fe177616f2c93f529f1a59717592debcca))


### Bug Fixes

* add more specific assertions ([610c2e2](https://github.com/complytime/trestle-bot/commit/610c2e2ee9ac2463f2fbc423b157747b9b21f412))
* check main binary in is_complytime_installed ([434ca80](https://github.com/complytime/trestle-bot/commit/434ca80b46bab3715d701a88e488c1e0596fd160))
* comment typofix ([ed9838c](https://github.com/complytime/trestle-bot/commit/ed9838cf64b3f0d7cd09355ba9f002ee7856817e))
* correcting unit test path reference ([94feff0](https://github.com/complytime/trestle-bot/commit/94feff0b41611a8347e6c819f2384fcced62e97b))
* CPLYTM-563: profile path resolved from cac profile name ([71b4066](https://github.com/complytime/trestle-bot/commit/71b40667e7c8d0d19e4887c66fcedbf01ee0a600))
* CPLYTM-710 updating logger statements ([778b529](https://github.com/complytime/trestle-bot/commit/778b5292b7469933c7c62b4231be354c3b6036e6))
* disable irrelevant semgrep finding ([ad698cc](https://github.com/complytime/trestle-bot/commit/ad698cc405b366b21341b736c6fbda37e4cf39ea))
* If OSCAL set-parameters filed is None, set to empty list ([eb75ae9](https://github.com/complytime/trestle-bot/commit/eb75ae9d66800fe151f0e779b64cab893d87a86a))
* introducing oscal-profile specific compdef directories ([12bfa32](https://github.com/complytime/trestle-bot/commit/12bfa3220ef28ea95c700006f6f2ce786bd0c875))
* remove dead code ([e3898f7](https://github.com/complytime/trestle-bot/commit/e3898f71b4d6b6fc5075d3910c8f3716e69dd787))
* rstrip strips characters, not strings ([58a8832](https://github.com/complytime/trestle-bot/commit/58a88327db9150385bda0c009f81a7db2539817c))
* terminal output suggestion ([9d206e7](https://github.com/complytime/trestle-bot/commit/9d206e793ec940e5ee313a92ac952e771f169da5))
* tests updated to resolve cac profile ([65890ad](https://github.com/complytime/trestle-bot/commit/65890ad306c50b726e8d586829305ab81a2007e4))
* updates logic to get release information ([#437](https://github.com/complytime/trestle-bot/issues/437)) ([93b910e](https://github.com/complytime/trestle-bot/commit/93b910edcc3f1afdceb7f3dc8ef8d1161932bb2a))
* updates sync_cac_content_catalog task to set empty values to None ([5de9ac6](https://github.com/complytime/trestle-bot/commit/5de9ac6c2c7914a17a2607e7aaae0008e98bc79d))
* updating if statement to extracting all controls ([50eadc1](https://github.com/complytime/trestle-bot/commit/50eadc148f80f6bbec061c992ebfd514710674ff))
* updating reference to profile in tutorial ([59118f6](https://github.com/complytime/trestle-bot/commit/59118f6761633ce93d854d75328d2b1f4ac49368))
* updating reference to profile in tutorial ([da69b8e](https://github.com/complytime/trestle-bot/commit/da69b8e2eef9f004873fc0e05528f97a425d0a24))
* updating the tutorial for compdefs ([215244b](https://github.com/complytime/trestle-bot/commit/215244b30c74132d9fd1a23f0a396900debdea62))
* use description from cac profile as prose ([#488](https://github.com/complytime/trestle-bot/issues/488)) ([d1db03f](https://github.com/complytime/trestle-bot/commit/d1db03f39616e929d7b8b47f1eb2c28b20fc2663))
* wrap kwargs ([0abb078](https://github.com/complytime/trestle-bot/commit/0abb078fb6114bea9f9df87b50d7d9d55a0bf481))
* yaml format error when sync OSCAL cd to CaC ([c50040e](https://github.com/complytime/trestle-bot/commit/c50040e8b570535264c2faf180662305a3b18cac))


### Maintenance

* add assert specificity ([5e2571c](https://github.com/complytime/trestle-bot/commit/5e2571c9ac697d06845d272436f804bb2e8e4084))
* add detail to error message ([25f766d](https://github.com/complytime/trestle-bot/commit/25f766dab61852bde43f57a5d09902cd362129d9))
* add get-github-release.sh script ([951c320](https://github.com/complytime/trestle-bot/commit/951c3209bfc899e56398ff301e7af475805a745b))
* add integration mark ([b300549](https://github.com/complytime/trestle-bot/commit/b3005499baae266111c6efc3c9525031fa90371c))
* add integration test stub ([a8e3da7](https://github.com/complytime/trestle-bot/commit/a8e3da71fdd7ad99a613eb9e76d0308140133be7))
* add test cases ([1fba546](https://github.com/complytime/trestle-bot/commit/1fba54649738d59c4a4f7c1aa9d6fc1cca086a83))
* CPLYTM-686 Remove duplicate catalog cmd ([37d4b7d](https://github.com/complytime/trestle-bot/commit/37d4b7da6eabfe483bccdaea4b76dc090a5c9bd4))
* CPLYTM-687 rename --policy-id by --cac-policy-id to make it more intuitive ([04e079f](https://github.com/complytime/trestle-bot/commit/04e079f6a7bcb8881bce85429d186898702eb789))
* disambiguate test-integration ([6960242](https://github.com/complytime/trestle-bot/commit/6960242161049c9509e905ebfa20a27405e1892a))
* extract function ([abc5297](https://github.com/complytime/trestle-bot/commit/abc529790fa7ca0e58cd085ef397b8c9a731bca4))
* format ([92d7608](https://github.com/complytime/trestle-bot/commit/92d7608ce3bd1dcbbf128f915228da338dc9621d))
* get profiles and controls are impacted by a rule ([4804092](https://github.com/complytime/trestle-bot/commit/48040920be3b3213b442ca758c38e635211680a7))
* get profiles and controls are impacted by a rule ([4f62857](https://github.com/complytime/trestle-bot/commit/4f628579da91974ec99a5132f4a2852a7808d36a))
* lint line length ([5074d84](https://github.com/complytime/trestle-bot/commit/5074d84cbc4fae0959f55b03fe79fd0074f042e5))
* port shell script to python ([c89d9c2](https://github.com/complytime/trestle-bot/commit/c89d9c2c678d92bb0964f2bfaf56a9a62bad37ec))
* remove dead code ([0c59ac5](https://github.com/complytime/trestle-bot/commit/0c59ac5375d9f1b40a16c1f8d867ce9fb01df805))
* remove dead code ([b297591](https://github.com/complytime/trestle-bot/commit/b297591782caf2462698eb0c787cb268fd88d656))
* remove the ignored SRG controls ([3515d92](https://github.com/complytime/trestle-bot/commit/3515d921d6c4d0185543f9a593713e8a69712d7f))
* remove unused comments ([d8d5b1e](https://github.com/complytime/trestle-bot/commit/d8d5b1e182b159a034ed219e7d837f1f05707de6))
* simplify pull request template ([93fcf7c](https://github.com/complytime/trestle-bot/commit/93fcf7c0a7408c37b3f5cdc711366425602c0223))
* simplify pull request template ([df081ad](https://github.com/complytime/trestle-bot/commit/df081ad16c01f1701a9b32ffedd01c2801891d4d))
* simplify return expression ([9e0dfff](https://github.com/complytime/trestle-bot/commit/9e0dfff4c5c424cca8f542c797513539bac43c9c))
* update docs ([88dcbd4](https://github.com/complytime/trestle-bot/commit/88dcbd4d1950a39679d4752112e69c883bdffdb7))
* update integration test paths ([846697e](https://github.com/complytime/trestle-bot/commit/846697eaf07f381b84797f9d6f403064da3c0270))
* update trestle version to 3.8.1 (fixes jinja vulns) ([#510](https://github.com/complytime/trestle-bot/issues/510)) ([d6653e5](https://github.com/complytime/trestle-bot/commit/d6653e5beb01f8847fcfc5281ae91e6b9e162c1c))
* use renamed cac-policy-id arg ([d3a3c34](https://github.com/complytime/trestle-bot/commit/d3a3c34b313be8947f8142119d39083617038d31))

## [0.12.0](https://github.com/complytime/trestle-bot/compare/v0.11.0...v0.12.0) (2025-03-07)


### Features

* 295 monorepo directory structure design proposal ([#389](https://github.com/complytime/trestle-bot/issues/389)) ([0314389](https://github.com/complytime/trestle-bot/commit/0314389ccb454b1c52ef68cd7670da97dbf62510))
* add a framework property to capture the CaC profile id ([#442](https://github.com/complytime/trestle-bot/issues/442)) ([0ceeb01](https://github.com/complytime/trestle-bot/commit/0ceeb01623d5c326bd9df9973622906856c0ef7c))
* add cac content rules transformation ([caaa44d](https://github.com/complytime/trestle-bot/commit/caaa44d0770b92b834d55fed1ee7204f7cd67be6))
* add control implmentations and implemented requirements ([3fe61d6](https://github.com/complytime/trestle-bot/commit/3fe61d6b722bae828a45bda8f478e9938cb7cfa3))
* add parameter transformation ([ce7b0d4](https://github.com/complytime/trestle-bot/commit/ce7b0d4491e0f76f7619b5ab8e023001f8ae7265))
* add sync catalog command ([d571394](https://github.com/complytime/trestle-bot/commit/d571394da11487500562bbabd6f372e034270c14))
* add unit test for validation component ([59016fb](https://github.com/complytime/trestle-bot/commit/59016fb52c2247c7c5a9702b0d986551efb443a9))
* **bot:** change for configuring trestle-bot PR body update ([#363](https://github.com/complytime/trestle-bot/issues/363)) ([812ae9a](https://github.com/complytime/trestle-bot/commit/812ae9acdc9741fc83e20cc219ecbb681e3bf6c4))
* CPLYTM-421 create validation component from rules ([e598832](https://github.com/complytime/trestle-bot/commit/e59883226a59872aab5cdc53bcc3cd9b79e5663b))
* CPLYTM-455 populate cac control status to implementation ([71db968](https://github.com/complytime/trestle-bot/commit/71db9680fd4d50d42213f4c31be2d05951786b39))
* initialize command for cac to oscal transformation ([6bc5073](https://github.com/complytime/trestle-bot/commit/6bc507319da7a01d1631f71345aa3a74705f484a))
* populate cac content product name as component title ([2ae3bb7](https://github.com/complytime/trestle-bot/commit/2ae3bb738ec283eb1c669d753be0191a5b284f2c))
* populate control notes into implemented requirement ([7e514e1](https://github.com/complytime/trestle-bot/commit/7e514e14d0195f146455bd3c481b05232f1a61bb))
* produces OSCAL Profiles by level ([#419](https://github.com/complytime/trestle-bot/issues/419)) ([dcbfa97](https://github.com/complytime/trestle-bot/commit/dcbfa9708a3defea670406b854bac85dfa2e4822))
* remove legacy entrypoints ([d2f41ad](https://github.com/complytime/trestle-bot/commit/d2f41adee4bbc7778f94cf3256028e5e3d37a643))
* update poetry.lock and add jinja macros ([65cc1c5](https://github.com/complytime/trestle-bot/commit/65cc1c5e6cb52e329bffb20426563fa7b8828ae0))
* update rule description value with rule title ([dd59a84](https://github.com/complytime/trestle-bot/commit/dd59a848141cf3aaf0f5e292feba538d180408a0))


### Bug Fixes

* a typo in autosync command ([d701aab](https://github.com/complytime/trestle-bot/commit/d701aab315e9f2ee6873ac9c324663681141e493))
* add sync-cac-catalog note ([42fb832](https://github.com/complytime/trestle-bot/commit/42fb832b91dd92bd391969c56dc85438796a33fb))
* broken link ([a90c9cd](https://github.com/complytime/trestle-bot/commit/a90c9cd0492c60cc586e2ac8a65252b6a2192800))
* do not include unselected rules ([47559a4](https://github.com/complytime/trestle-bot/commit/47559a449c30eb960948cfd998bc0da87c0c848a))
* fix a typo in cli root ([b7b511e](https://github.com/complytime/trestle-bot/commit/b7b511e173aea8ad9f7c2681b6ea0e640a88e05a))
* fix github doc and templates ([c9333b6](https://github.com/complytime/trestle-bot/commit/c9333b6f90cf19b8836b8aa88f8554472d76a7a6))
* fix test failure in validation component ([f6f8d19](https://github.com/complytime/trestle-bot/commit/f6f8d192a98fb83f4e0498c7699a242baf95e428))
* format ([fdef810](https://github.com/complytime/trestle-bot/commit/fdef8107e3b48b6c93455bf3084c91aceaf2810f))
* improve the validation components with parameters ([27b0733](https://github.com/complytime/trestle-bot/commit/27b07334bd7394fb26c46203e2b29408782b02ac))
* lint ([5f1adcb](https://github.com/complytime/trestle-bot/commit/5f1adcb24e1c16885047d7c34a126f81a7daf3df))
* lint errors ([86b7f87](https://github.com/complytime/trestle-bot/commit/86b7f87623ac848e5e120c33fcbfa586f5f45b0f))
* list index out of range error ([a62c247](https://github.com/complytime/trestle-bot/commit/a62c2477b72948e75e3f9b16bea9cdf9d781781d))
* mangled doc update ([85840bb](https://github.com/complytime/trestle-bot/commit/85840bbe7f8b46f5b651c2a7251a6262a5e7bd01))
* massage cac data into oscal format ([ba94097](https://github.com/complytime/trestle-bot/commit/ba94097acea22d7c3235b1be6290115b86a69a5e))
* run the paths-filter step in its own job ([#370](https://github.com/complytime/trestle-bot/issues/370)) ([cb42cfe](https://github.com/complytime/trestle-bot/commit/cb42cfe7e2a5d554f7380a4b327a09324a8d3834))
* specify click path_type ([6a911f5](https://github.com/complytime/trestle-bot/commit/6a911f569b971903e2fd440b564a3ba7d041e34f))
* support older Python versions ([9b5282a](https://github.com/complytime/trestle-bot/commit/9b5282a1e6331f0767b3e51cb5537c017437912c))
* sys.exit with errorcode when exceptions ([2c2df3d](https://github.com/complytime/trestle-bot/commit/2c2df3d589750ac1a8af763b139a2e21b70bb59c))
* trim whitespace ([2082079](https://github.com/complytime/trestle-bot/commit/2082079ed645f32d7cd587a61921c4cfce2eef96))
* try to work around conflicting CI rules ([e5d4431](https://github.com/complytime/trestle-bot/commit/e5d4431ddca8ce874ab3f0729689caa30ee64808))
* unit tests in pycharm ([42f3b96](https://github.com/complytime/trestle-bot/commit/42f3b963d06d86a7d5e132984c00001d7b9cc12f))
* update create command for e2e testing ([abcd7eb](https://github.com/complytime/trestle-bot/commit/abcd7ebbf87464e46f7161bb991b8963d70a4784))
* update e2e test to use new commands ([6e70243](https://github.com/complytime/trestle-bot/commit/6e7024315f75851e6bd76affc8544ea4eac933ea))
* use ControlsManager to load policy ([71e040d](https://github.com/complytime/trestle-bot/commit/71e040dcbebd3c96f4f2ef52cd2dc8d14c2ea21d))
* use original CaC id on label ([9a99c7e](https://github.com/complytime/trestle-bot/commit/9a99c7eb2d7c011fe4bab6564b628da09b88dd97))


### Maintenance

* add notice regarding repo org move ([#413](https://github.com/complytime/trestle-bot/issues/413)) ([c17fbee](https://github.com/complytime/trestle-bot/commit/c17fbeedb7afdff9f88692824d10a2b2d298c7a1))
* add openssf scorecard workflow ([#359](https://github.com/complytime/trestle-bot/issues/359)) ([63ed23c](https://github.com/complytime/trestle-bot/commit/63ed23c1768b49022b71b03dcda58fe1b001a452))
* allow lower case in PR subject ([#406](https://github.com/complytime/trestle-bot/issues/406)) ([73351bc](https://github.com/complytime/trestle-bot/commit/73351bc7c9cd1cb719036fc9fca3acc8a4844449))
* create a minimalist macro file for unit tests ([edb82f0](https://github.com/complytime/trestle-bot/commit/edb82f03c4ec5d38b904cf2ebe6170849b23bee4))
* load CaC Policy by id without ControlsManager ([4e71cc7](https://github.com/complytime/trestle-bot/commit/4e71cc71c741a853866948406809d83e22841839))
* make trestlebot/cli/root.py executable ([0f74955](https://github.com/complytime/trestle-bot/commit/0f74955eb91b1499558cb4d130c13845cc1fc363))
* merge control resolvers from different modules ([b3c77f4](https://github.com/complytime/trestle-bot/commit/b3c77f4baa09fb99d6cfe3f5a9da516705d7877a))
* move sync-cac-catalog to sync-cac-content ([8a1af94](https://github.com/complytime/trestle-bot/commit/8a1af94f6c495f4be544efe01030352b14838f9b))
* remove macros not relevant for current tests ([fe819c8](https://github.com/complytime/trestle-bot/commit/fe819c829a04825946bde48729d619c9f35e4855))
* rename rule-transform to rules-transform ([226a0d2](https://github.com/complytime/trestle-bot/commit/226a0d24c1fd83a3101bfd251deac3a850143569))
* split create or update component definition function ([84529b3](https://github.com/complytime/trestle-bot/commit/84529b3e1796774ff8e8e6775ae3619d2765cf22))
* start local e2e testing docs ([424dd55](https://github.com/complytime/trestle-bot/commit/424dd558ac16962da0b478dff535a43e923c3417))
* transformation performance improvement ([debfd95](https://github.com/complytime/trestle-bot/commit/debfd954c044eddec7b3e7aab92f275e7a214aa9))
* update actions for debug and config options ([1f16ca3](https://github.com/complytime/trestle-bot/commit/1f16ca301da9b808568e671f0b7a3f99f26ddb99))
* update actions with new cli design ([487d1d4](https://github.com/complytime/trestle-bot/commit/487d1d40ec4db1502e2ad11344b71d01cce5e12b))
* update checking on component data ([3a2ea5d](https://github.com/complytime/trestle-bot/commit/3a2ea5d24f7dcc367a76b5858abf267589b2a292))
* update command list ([c18c55f](https://github.com/complytime/trestle-bot/commit/c18c55f22c1d9ae7b89eedcd012656b69a64f33c))
* update docs for sync-cac-content catalog ([aba8001](https://github.com/complytime/trestle-bot/commit/aba800182198141ca2a42cc5523d70502aaa34b6))
* update pyproject.toml entrypoints to cli root command ([64adaf5](https://github.com/complytime/trestle-bot/commit/64adaf5002df6e316db9da9b54ee6cea9633a4fd))
* update SyncCacContentTask ([1506fee](https://github.com/complytime/trestle-bot/commit/1506fee09bfaf426004c3e637e5f17792089061d))
* update testing for sync_cac_content ([76d7f9b](https://github.com/complytime/trestle-bot/commit/76d7f9b88af125f1c72bdaec47d117b83da0f49e))
* use trestle API to get catalog path ([e923009](https://github.com/complytime/trestle-bot/commit/e9230097524cb2c573e2c3f82a86d2174edfd8d5))
* wording improvement ([2f6ed28](https://github.com/complytime/trestle-bot/commit/2f6ed28c2d34ccae09b9ab85d647c7ff42381c6a))

## [0.11.0](https://github.com/RedHatProductSecurity/trestle-bot/compare/v0.10.1...v0.11.0) (2024-09-25)


### ⚠ BREAKING CHANGES

* default module entrypoint is now the init command
* Modifies the existing behavior of the rules transform entrypoint

### Features

* adding init command to entrypoints ([#326](https://github.com/RedHatProductSecurity/trestle-bot/issues/326)) ([868c1fa](https://github.com/RedHatProductSecurity/trestle-bot/commit/868c1fae3bb2fa85df734905aa38b33dc37c9b47))
* adds markdown generation to the rules transform entrypoint ([#282](https://github.com/RedHatProductSecurity/trestle-bot/issues/282)) ([84dec70](https://github.com/RedHatProductSecurity/trestle-bot/commit/84dec70d7810abf7306b708104b4c7bf682a49ad))
* removes provider from init and moves CI templates ([#344](https://github.com/RedHatProductSecurity/trestle-bot/issues/344)) ([21b4043](https://github.com/RedHatProductSecurity/trestle-bot/commit/21b40432f446323ded883c248feaa064ea1cabd6))
* tutorial for GitHub and init command ([#333](https://github.com/RedHatProductSecurity/trestle-bot/issues/333)) ([6334c1f](https://github.com/RedHatProductSecurity/trestle-bot/commit/6334c1f16fffa94bacbb250c95f754ed80abff9b))
* update module default to use init entrypoint ([#329](https://github.com/RedHatProductSecurity/trestle-bot/issues/329)) ([d1490cb](https://github.com/RedHatProductSecurity/trestle-bot/commit/d1490cbde72b204875260cd210f61760e9f3c056))
* updates SSP generation to include all parts ([#348](https://github.com/RedHatProductSecurity/trestle-bot/issues/348)) ([18c6600](https://github.com/RedHatProductSecurity/trestle-bot/commit/18c6600a47d9833811a045fa60e167608f06a180))


### Bug Fixes

* add markdown-include package to workflow and poetry ([#339](https://github.com/RedHatProductSecurity/trestle-bot/issues/339)) ([c7a05ee](https://github.com/RedHatProductSecurity/trestle-bot/commit/c7a05eebe87f853a435b31abadba8db05d2458a2))
* updates dependabot prefix for conventional commits ([#308](https://github.com/RedHatProductSecurity/trestle-bot/issues/308)) ([ee86f5c](https://github.com/RedHatProductSecurity/trestle-bot/commit/ee86f5c35755686d3fc3adf6ca94e1c4ac8d873e))
* updates e2e tests checkout ref during image publishing ([#334](https://github.com/RedHatProductSecurity/trestle-bot/issues/334)) ([5439b91](https://github.com/RedHatProductSecurity/trestle-bot/commit/5439b91c7b0ed1d75c7a5ec3f2b3f4e94ea5968a))


### Maintenance

* change dependabot frequency to weekly ([#290](https://github.com/RedHatProductSecurity/trestle-bot/issues/290)) ([3da37f7](https://github.com/RedHatProductSecurity/trestle-bot/commit/3da37f7b69538e157b5b48b461140d0f9bfd6d9d))
* **deps:** adds compliance-trestle-fedramp dependency ([#349](https://github.com/RedHatProductSecurity/trestle-bot/issues/349)) ([aeb6e0c](https://github.com/RedHatProductSecurity/trestle-bot/commit/aeb6e0c59bb0e09ee2142f886e9682a8f8e118e6)), closes [#318](https://github.com/RedHatProductSecurity/trestle-bot/issues/318)
* **deps:** bump trestle to version v3.3.0 ([#269](https://github.com/RedHatProductSecurity/trestle-bot/issues/269)) ([a2a2db6](https://github.com/RedHatProductSecurity/trestle-bot/commit/a2a2db6bbbcac2bec23b9fe520a0958afc488616))
