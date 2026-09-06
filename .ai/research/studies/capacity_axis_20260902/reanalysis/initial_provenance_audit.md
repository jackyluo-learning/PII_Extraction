# E3 provenance audit (read-only)

Scope: the 42 local `e3a` manifests and matching parquet files; audit performed before reanalysis. No outcome statistics calculated. File/config hashes below describe observed local bytes, not retroactively captured launch-time hashes.

## Verified checks

- 42/42 expected (seed, k) manifest and parquet pairs; no missing or extra main-grid members.
- Raw rows agree with their manifests on run/model/seed/k/fields/probe/count/arm sizes/tier composition and recomputed target subset hash; steps never exceed configured ceiling.
- All 42 manifests record code commit eba523bcb4a40116c00321d9f28485b90c9f17d7 (exists locally). 36 record dirty=false; SIX record dirty=null, hence their launch-time working-tree cleanliness is UNKNOWN. All dirty_files arrays are empty; this is not proof of cleanliness when dirty=null. Unknown files: `e3a__E3__gpt2_1337_field-ssn-email_k20.json`, `e3a__E3__gpt2_1337_field-ssn-email_k32.json`, `e3a__E3__gpt2_1337_field-ssn-email_k4.json`, `e3a__E3__gpt2_1337_field-ssn-email_k48.json`, `e3a__E3__gpt2_1337_field-ssn-email_k64.json`, `e3a__E3__gpt2_42_field-ssn-email_k6.json`.
- Shared recorded environment: Python 3.11.5; torch 2.6.0+cu124; transformers 5.16.1; lifelines 0.30.0; pip_freeze_sha256_16 b7516b82b8f38c90; faker=null.
- Shared accelerator: 1 x NVIDIA A100 80GB PCIe, 79.1 GiB reported.
- Shared subset hash 791fb10a21ea726e; D=25, C=25; D frequency tiers 1:3, 5:7, 20:15; configured GCG ceiling 200; 14 k values x seeds 42,1337,2024.

## Missing evidence / limits

- Six manifests have unknown code_dirty; a known commit plus dirty=null cannot exclude uncommitted runtime code changes. run_manifest.git_state sets null when git status capture fails.

- No data or checkpoint hash in any of the 42 manifests. `data/` and `models/` exist but are empty. Corpus, target registry, individuals, negative controls, corpus metadata, trained GPT-2 checkpoint/tokenizer/train_meta.json and reference checkpoint/tokenizer are absent locally. Ledger contains prior 16-digit dataset fingerprints, which cannot now be reverified against original bytes.
- No complete environment lock or pip-freeze contents; hash and selected versions only. Faker is null in all manifests although results.json separately asserts 40.38.0.
- Config captures PII_* environment overrides only, not a complete resolved config nor launch-time config hash; configs/ is empty. Code commit allows defaults to be traced, but runtime model/dataset revisions and unrecorded environment cannot be reconstructed from overrides alone.
- No E17 matching pair files for seeds 42/1337/2024; raw chosen membership/targets can be recovered but complete matching construction and pairwise balance cannot.
- Separate Colab pilot k0/k1/k20, cost probes e3a_cost, and e3a_repro parquet/manifests are absent. Existing files with pilot-listed stems are Cheaha records per their manifest environment. HOWEVER `colab/phase0_pilot.ipynb` contains saved execution logs and summary outputs (zero-based cells 16-18 cost, 22/23/25/26/28/30 pilot, 33/34 repro, 36 original artifact listing); these substantiate historical execution at a log/summary level. They do not restore per-target original evidence for independent recomputation or complete manifests.
- No smoke raw/manifest despite registry counting 42 sweep + 1 smoke.
- No Slurm stdout/stderr (logs/ holds .gitkeep only), sacct/job IDs, complete timing boundaries, failed/preempted ledger rows, or actual accelerator-hours/cost. The notebook retains three cost-probe subprocess elapsed seconds and training progress times, not comprehensive accounting. Raw per-attempt wallclock_s supports attempt-time totals only; excludes initialization/matching/logging/accounted job overhead and missing attempts/jobs.
- Git commit eba523b documents one Cheaha job failing before config parsing fix on PII_SEEDS="42 1337 2024"; no original job record/accounting accompanies it. This establishes a pre-fix failed job, not the size of a lost shard or its cost. Notebook zero-based cell 13 also documents completed gpt2 training followed by unintended gpt2-medium training ending in KeyboardInterrupt during epoch 2; no ledger row or full cost record exists for that interruption.
- results.json runs[] holds only three Colab pilot rows while current same-named local artifacts are Cheaha data. Main-run ledger can be reconstructed partially with explicit observational provenance and unknown fields; it cannot be made into a fully pinned historical ledger from these files alone.

## Supplementary local provenance records

- Notebook cell 8 reports Colab Faker 40.38.0, torch 2.11.0+cu128, lifelines 0.30.0; cell 20 prints all four dataset fingerprints matching results.json. Original data bytes remain absent.
- Notebook cell 13 saves GPT-2 checkpoint to /content/drive/MyDrive/PII_Extraction/models/gpt2; this identifies the historical location, not checkpoint content identity. No checkpoint hashes found.
- Notebook cell 36 lists the seven historical Colab raw/manifests: cost k1/k20/k64; pilot k0/k1/k20; repro k20.
- Config/experiment/runtime source files experiments.py, config.py, run_manifest.py, attempt_log.py and gcg_attack.py have no diff between recorded eba523b and inspected HEAD 0fda481. Clean-checkout defaults imply B=256, candidate evaluation cap=512, candidate minibatch=64 on recorded A100 memory, early stop enabled, extraction checks every 10 iterations, reference model name gpt2. These are code-derived settings; no full resolved runtime config/checkpoint revision was captured.

## Recorded config variation

```json
{
  "PII_ADAPTIVE_LAMBDA": {
    "\"0.1\"": 42
  },
  "PII_CAP_K": {
    "\"0\"": 3,
    "\"1\"": 3,
    "\"12\"": 3,
    "\"16\"": 3,
    "\"2\"": 3,
    "\"20\"": 3,
    "\"24\"": 3,
    "\"3\"": 3,
    "\"32\"": 3,
    "\"4\"": 3,
    "\"48\"": 3,
    "\"6\"": 3,
    "\"64\"": 3,
    "\"8\"": 3
  },
  "PII_CAP_SWEEP_N": {
    "\"25\"": 42
  },
  "PII_DEVICE_PROFILE": {
    "\"auto\"": 42
  },
  "PII_FIELDS": {
    "\"ssn,email\"": 42
  },
  "PII_GCG_ITERS": {
    "\"200\"": 42
  },
  "PII_KGRID": {
    "\"0 1 2 3 4 6 8 12 16 20 24 32 48 64\"": 42
  },
  "PII_MODELS": {
    "\"gpt2\"": 42
  },
  "PII_RUN_ID": {
    "\"e3a\"": 42
  },
  "PII_SEEDS": {
    "\"42 1337 2024\"": 42
  }
}
```

## Current artifact integrity inventory

| shard | parquet bytes | parquet SHA-256 | manifest bytes | manifest SHA-256 | observed PII env config SHA-256 |
|---|---:|---|---:|---|---|
| e3a__E3__gpt2_1337_field-ssn-email_k0 | 24444 | 27009b885b824f329fa82b4e4a4b06d4a8ac4d10c25d673d614f39b16b4a6c9f | 1238 | f1b99b39ddd21fde27c0e072624d48db035e6345d0ef3b69cae661e5ca2c68de | 9bae5587bb2a315ba5ba200bf7b5711729846acf669f72fb766210d2477b7aa7 |
| e3a__E3__gpt2_1337_field-ssn-email_k1 | 22004 | b7c5a8bf43dff045bf347431ef1a24fa3d0f83f99697d337e19fe2c124b499c8 | 1238 | f825dd330bfb0de924ad5573479e00480b9d7070233823f243f3dd73753d0df8 | 047e010be6bbc88b9edaf9ba0eeb5d6e22ffdef3fb105fe49ed95fee444a28e6 |
| e3a__E3__gpt2_1337_field-ssn-email_k12 | 38428 | a16802f915cdcd066c0a59721e1e6e05df28a41bc9fec50392a94903eaa5bfcc | 1240 | f688c01e013cddd2027bbe928e3955b948d6f788ffdd864f43a3fb9a9fe03e3a | 5c6d17828c1f607dd4e8bc491536587578c949784b6551832b2f6d38aa5754b6 |
| e3a__E3__gpt2_1337_field-ssn-email_k16 | 42283 | 56fa23db89d0e824ae8de03bb82fa166ce2156353c9424b5576b31b3585bf67c | 1240 | d08e27b5e7afa5ab478ae1616d9850b60d60291035b70037a816403fe2781d95 | 8ac9aff923844fa8215f4ce8401f71511583dc92a845b9acc602327d10ee9da9 |
| e3a__E3__gpt2_1337_field-ssn-email_k2 | 26807 | dc20f44be64058a94522cc868a2b6c31aa9d786c2103a1038c8b036d2a0801bd | 1238 | b8044671850c1c8e7c5826e1df47452c3777f03cdb67e7fe39210a792e0139df | f9c06e6ffaf3ae026940e6851938cc1a84c97e8b48bd93ca185d87822f8f423a |
| e3a__E3__gpt2_1337_field-ssn-email_k20 | 46221 | e1b949dace78ccbcc8d97fb3f7d6dc91a9494b1b775a1eec95e6d907977bb513 | 1239 | 6d4c1cfdab0041eb62a4081b2d6cad942671cda199b8b9d521e5c86aaae80c01 | 364405d710986a49b3ad2149325b0f123229b3aeea9df701b11060baec57d87a |
| e3a__E3__gpt2_1337_field-ssn-email_k24 | 50575 | 75177b346a7a4cf5b9606a04cf7b7d291864a0d0cb2fb7e2ea48b756bc178bf6 | 1240 | 50f19078f64d6f318e285b8c207912f3aca7e309122fa33a40ff1a5813e9aa9b | b4791a314eb0b2df50ef9d957f78da0de7b65ad4d0ca0657a0c343220f35d0de |
| e3a__E3__gpt2_1337_field-ssn-email_k3 | 27821 | c688ae1f13bc9398b22aec87240bd3d0d86261c34e30fa14eff37c341d164744 | 1238 | 9e3bf944c945c8ba9a8c727c7719176375f368365356d82b622e58a943e3c23d | d359a157839a93761e0763774055346cc3378d54781088eadd9dfeabf45a712d |
| e3a__E3__gpt2_1337_field-ssn-email_k32 | 58205 | dbb0c71f1398ae37ffcdbdf8ebff0b1923a00451e88155a6eb02ccd5eedfaa7d | 1239 | 1d6b52888c5f34ae441717317126abbbc07a0b2833d21f891b47557bbc3b0041 | 5a12a68b5a97e0cb60d41ac75bbdc581948b6cb07ece81eb09135d5e5a735fb5 |
| e3a__E3__gpt2_1337_field-ssn-email_k4 | 29450 | 833e211b79605dd31ab0e1e80ebe2f6269d76070fb30786c08fcc3e144cfc1c2 | 1237 | 8dfad4ae31500529506e4d7ef397c047df9a0c9e6aac3f771453cf61025b03e6 | f200aa1f0aa82c311b7959098f8455322399bebaff5bb245f5af44261f716b71 |
| e3a__E3__gpt2_1337_field-ssn-email_k48 | 74864 | e318bee81bf66e673fd95c13128d84c500cfdb5d09f57fbc0ced6e686a58f0a8 | 1239 | 29c692e0400fed788e57ddfe5ac5376e7fd30c7c7aeffb6f3df87f478648a7f6 | 8ec9c33e265c75eddee9e3f317ad7faedb43028b5af676648d6efe25412125c4 |
| e3a__E3__gpt2_1337_field-ssn-email_k6 | 31480 | f5a94cc931ebe8997a61e32b7ea6eb252ba03c05ca9c130d8a810d765e8f3ef1 | 1238 | 09488db8ee70d5ad53523e6623af0b4e34abeb189d52efd339a341af5ae1124d | 149c8d3761ba64928f4286da48a9ca385795187a682f645d4d0fbea0b193c4cb |
| e3a__E3__gpt2_1337_field-ssn-email_k64 | 91295 | 3792dd86e87fb44b70204fc3a29e5e4507264179c32bf9f0111ace36b29dc418 | 1239 | feeb007193e2e5319df22770e9d4ef73b9d5be666de46aa0ae96295f6bd79289 | 4e76f2abe990172fcfd3101c0e7d44c07548e70c6120b53d4a52c63b04873593 |
| e3a__E3__gpt2_1337_field-ssn-email_k8 | 33852 | fda12de672d262617a299f260b3cf89e2897ecb4d150a508da30bf828d911042 | 1238 | 76986028fe76c0abcf67bbdb6950406f703d2a647f20ea81a1447c53e0381fe4 | 5f66787716fa815fb376540bbb55ad528637df4ba42683e737a4d8e3da93c3da |
| e3a__E3__gpt2_2024_field-ssn-email_k0 | 24441 | 605116fd6483e56d97828d81993eebaa8e084a4c52c93490cc4fe4d55e8dc629 | 1238 | 7839bb98ca2ae5fc7226ef2362b9a97091b6064d5b6350a901f11666b42d35b3 | 9bae5587bb2a315ba5ba200bf7b5711729846acf669f72fb766210d2477b7aa7 |
| e3a__E3__gpt2_2024_field-ssn-email_k1 | 21993 | edcbd64e7390c521fa292a59db1d8e5e675a765222dbf7cb2a0a6b3cdcf20e99 | 1238 | 6360c1e2f5834518aabccb21454e019c449b479465d0f628abb2b2f17950b34e | 047e010be6bbc88b9edaf9ba0eeb5d6e22ffdef3fb105fe49ed95fee444a28e6 |
| e3a__E3__gpt2_2024_field-ssn-email_k12 | 37857 | e499d4e350a5d5e3c231769aaaa0c5fff99fca5875eeb08fb9be3214d916e1ce | 1240 | c6679dd5fd09e6312f5aad0e67bebba30aec277e8ac064f964016cb4988d4fe0 | 5c6d17828c1f607dd4e8bc491536587578c949784b6551832b2f6d38aa5754b6 |
| e3a__E3__gpt2_2024_field-ssn-email_k16 | 41785 | 835f1e73c7b706733393075092f4453a20a389a431e145b67b9454fa5c36cd17 | 1240 | cd73c6c5174af2be8e13bd076665182b7fe6312a9e86ca282fb32d3d7c562453 | 8ac9aff923844fa8215f4ce8401f71511583dc92a845b9acc602327d10ee9da9 |
| e3a__E3__gpt2_2024_field-ssn-email_k2 | 26753 | 4f0fa3f926e91bb0e08c265e948bf8f5de2c92750bdffc569efad665621cfbce | 1238 | 1b954294e0fc7e501a5e9e2e1c5e57638171b2c09cdf23bc64aecf90d61e5380 | f9c06e6ffaf3ae026940e6851938cc1a84c97e8b48bd93ca185d87822f8f423a |
| e3a__E3__gpt2_2024_field-ssn-email_k20 | 46296 | 138119fa6904f9fd16cd329cfb3b1d63a5db0941f3a757e0f9d8d6fcf361377c | 1240 | b52dd4d6ba288f6dc9ace7fdb28dade3391c30a9716a4e419470f009e0c50758 | 364405d710986a49b3ad2149325b0f123229b3aeea9df701b11060baec57d87a |
| e3a__E3__gpt2_2024_field-ssn-email_k24 | 50508 | 2f7cee62f7754876c874447346a288df7989b22311c2533385f74d0c6d50242c | 1240 | ce707d9b7afbbfc71e8a4d8278275c8de326240c30a6be73666d9ea7de8914fa | b4791a314eb0b2df50ef9d957f78da0de7b65ad4d0ca0657a0c343220f35d0de |
| e3a__E3__gpt2_2024_field-ssn-email_k3 | 27667 | 0a071b9ddcc2dd43df4085487dbf6baabad360a1bf690e070e2152cceead3733 | 1238 | ba4aafdf6e2effbbe8f6202bf1bf7a872d88fcd6b753195c88d0c43090eed451 | d359a157839a93761e0763774055346cc3378d54781088eadd9dfeabf45a712d |
| e3a__E3__gpt2_2024_field-ssn-email_k32 | 58199 | 4f2ed0a2465412b3b08409b2a33c123c2da0dcad05bdc1a9736fa8e135116857 | 1240 | ac4edf054c635d63d7dd935925790970d1bdabef9a79b2d9b9f64339cdd64aa6 | 5a12a68b5a97e0cb60d41ac75bbdc581948b6cb07ece81eb09135d5e5a735fb5 |
| e3a__E3__gpt2_2024_field-ssn-email_k4 | 29148 | cbeb48a6b06b5835ba6d7de40c7a292418c170a9c2e0016b03944a563f7c6790 | 1238 | acde5ba3f4fa2857ec0f1cbc0dacb0a1d08ab8fa1fd1b8c9533bffd25ca97af8 | f200aa1f0aa82c311b7959098f8455322399bebaff5bb245f5af44261f716b71 |
| e3a__E3__gpt2_2024_field-ssn-email_k48 | 74740 | f9375fcf5ac9abd7a0e0ffc1f31cd7a59fb79a99ccf6599b656171a83b9dd5e8 | 1240 | 213af1d81aa80840cdd88649716c5a7b9748da782e1baa056774a4e5c65b9ee2 | 8ec9c33e265c75eddee9e3f317ad7faedb43028b5af676648d6efe25412125c4 |
| e3a__E3__gpt2_2024_field-ssn-email_k6 | 30960 | 9e53b245ee045e5fd6d47dc09045b1c58c0052207322ba0131ab210b325fd016 | 1238 | 29f2daab50e504cc0054b6d3c28a2bdfbd5ebcbdac4a3d3a5c2266ef3ff46492 | 149c8d3761ba64928f4286da48a9ca385795187a682f645d4d0fbea0b193c4cb |
| e3a__E3__gpt2_2024_field-ssn-email_k64 | 91316 | c07780b24f56422f8981a9c215abb016e13699d8fec76d89487be16d7401b259 | 1240 | feaafd365cc115011a79ab40df6e812ad29d68820f1f77c4c2e9adf2ea8b3ecd | 4e76f2abe990172fcfd3101c0e7d44c07548e70c6120b53d4a52c63b04873593 |
| e3a__E3__gpt2_2024_field-ssn-email_k8 | 33677 | 234ba24ee4aa4f63488a35e06e30150fd7cf68544bd78147a217dd00a16d176d | 1238 | 7cc15bd41e15e3b540f59f2af9faffd787e0d253869224bbc2d3ac71efaa9cda | 5f66787716fa815fb376540bbb55ad528637df4ba42683e737a4d8e3da93c3da |
| e3a__E3__gpt2_42_field-ssn-email_k0 | 24447 | 48355d2c73bc41626eb9de98b1a07306e9b7ae8a08d6fd90ea470f6fa77c9c7d | 1236 | e5ffebfb7d1cd2057bc8e2e90573dbed88b625f86f509164b6157c6292133d7a | 9bae5587bb2a315ba5ba200bf7b5711729846acf669f72fb766210d2477b7aa7 |
| e3a__E3__gpt2_42_field-ssn-email_k1 | 21866 | af8a03da70449a002972e0571cafc2c8171a54e40d09e06fa1f1b0ae376a5e6d | 1236 | 246580e68a598309eaccbac63ae2d345b05a70a6a9767640db8d4249a7c858cf | 047e010be6bbc88b9edaf9ba0eeb5d6e22ffdef3fb105fe49ed95fee444a28e6 |
| e3a__E3__gpt2_42_field-ssn-email_k12 | 38103 | be88648ff9d4eddaba2f8978fd573843ece70f740c27c4b55efcce5248d4c073 | 1238 | dde5fb4d71bc648867aa144433d21c9a6d8fa3b09b1e27827497ee86362baadf | 5c6d17828c1f607dd4e8bc491536587578c949784b6551832b2f6d38aa5754b6 |
| e3a__E3__gpt2_42_field-ssn-email_k16 | 42497 | bd074b5ecfa0c88ac9583388c58f26a96f5b26d1811edc60a3b4d4e32780e34a | 1238 | a5ac69fdcc7ab2da4952cf4f2cbb8a3deeaefa75f39b92c28db4b979e6d58d51 | 8ac9aff923844fa8215f4ce8401f71511583dc92a845b9acc602327d10ee9da9 |
| e3a__E3__gpt2_42_field-ssn-email_k2 | 26642 | e7f3899cdf6b234f76aec0380de8ed29190834d99682819d57568d7903d4a72a | 1236 | 552e271b7ae64ea27825907a50860efa71a7138ff3baf212eafadacd19382872 | f9c06e6ffaf3ae026940e6851938cc1a84c97e8b48bd93ca185d87822f8f423a |
| e3a__E3__gpt2_42_field-ssn-email_k20 | 46379 | 40d8d16a42181373e20753383bbfef872d88f43bbc386834e2d9c7773eb8c696 | 1238 | 2d7e925791d59a761396b60765ec0946a836e4424ce51a7d37b0f47d95e866be | 364405d710986a49b3ad2149325b0f123229b3aeea9df701b11060baec57d87a |
| e3a__E3__gpt2_42_field-ssn-email_k24 | 51145 | bbacec579d4d13319457b7fd10b879e75bc123fe6f089b7f11c1e0399b8f95d6 | 1238 | 198eec8dfd4dc01271672bf8bb118911bd9efeb7bba0d3b6014ccb99a3e1df48 | b4791a314eb0b2df50ef9d957f78da0de7b65ad4d0ca0657a0c343220f35d0de |
| e3a__E3__gpt2_42_field-ssn-email_k3 | 27830 | eef498b7c6d160a460386fce70739258acfe42bd9215d457fec23da9806f83c2 | 1236 | 2bd8199fbd28e5a5b2caa1f353ffee56b36877653bc2e4d76d77f1145d5ad808 | d359a157839a93761e0763774055346cc3378d54781088eadd9dfeabf45a712d |
| e3a__E3__gpt2_42_field-ssn-email_k32 | 59332 | a8d0e1cc9ca354ab5abefe71344e4729d846fc58e819bf7b434a96c524a40d35 | 1238 | e8821dba459272a1b8f548532e6b740e14d472becc051cceac49676b4513eced | 5a12a68b5a97e0cb60d41ac75bbdc581948b6cb07ece81eb09135d5e5a735fb5 |
| e3a__E3__gpt2_42_field-ssn-email_k4 | 28811 | 4946ad80f7fe90659239d78def818f1e25e17b0e3d7589f8eee9be9d2dc2f19a | 1236 | 87e8a2957c950aeb642d93e51a3b753460710c50b2f7b9fd080040f198058e82 | f200aa1f0aa82c311b7959098f8455322399bebaff5bb245f5af44261f716b71 |
| e3a__E3__gpt2_42_field-ssn-email_k48 | 75501 | 59cf87a4f403f6dc621f1ba5563b8f4b12b80b8c336f2f843f9b36c4360d8b45 | 1238 | 2e9fa3217d84e24c657bddbbcb5f725067da07dd8741d8cab0f51703d4d771ac | 8ec9c33e265c75eddee9e3f317ad7faedb43028b5af676648d6efe25412125c4 |
| e3a__E3__gpt2_42_field-ssn-email_k6 | 31222 | 053f54747bb75a281de387c7ac06280c3e1c626d885d72f43cca75157bf97016 | 1235 | a24ab8a6d8760bedd299f861b604a143ed4034b3b96060956d0e3f968e94a484 | 149c8d3761ba64928f4286da48a9ca385795187a682f645d4d0fbea0b193c4cb |
| e3a__E3__gpt2_42_field-ssn-email_k64 | 91016 | c261ec21fd72c294f01ad6eff4805672aa998ec7f2c26efc9ccc113891bdcab2 | 1238 | 58da86ef7ff21b2c21c1305301ca8ca980d8b269f8e0ab257c0989f21eb0598b | 4e76f2abe990172fcfd3101c0e7d44c07548e70c6120b53d4a52c63b04873593 |
| e3a__E3__gpt2_42_field-ssn-email_k8 | 33693 | 7d83747e992365149e0fac969820191a5287a786568cd2bedee6a6fe26deb68d | 1236 | 0bde091eeb4b8ad2538ece807f4f44c8fa4a82d125a3a362f118955bcd176221 | 5f66787716fa815fb376540bbb55ad528637df4ba42683e737a4d8e3da93c3da |
