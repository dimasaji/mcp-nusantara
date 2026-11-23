# Lokasi bukti dan reproduksi

Semua perintah uji dijalankan pada Windows. Interpreter: C:\Users\dmaza\mcp-starter\.venv\Scripts\python.exe. Source snapshot final: C:\Users\dmaza\mcp-starter\.tmp-build\pc-stabilization-20261123\source. TEMP/TMP: C:\Users\dmaza\mcp-starter\.tmp-build\pc-stabilization-runtime. PYTHONPATH memilih snapshot/backend dan snapshot/tests; paths worker IndoBERT memilih interpreter dan worker primary yang sudah ada. HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE aktif. Tidak memakai database atau .env live untuk full suite.

Full final: python.exe -u -B -m pytest tests -o addopts= -p no:cacheprovider --basetemp=C:\Users\dmaza\mcp-starter\.tmp-build\pc-stabilization-runtime\suite-temp-06 --junitxml=../suite-06.xml --tb=short --disable-warnings -vv

Log/JUnit: .tmp-build/pc-stabilization-20261123/suite-06.log dan suite-06.xml. Run 03–05 dipertahankan terpisah. Model Ollama lokal sementara sudah dihentikan; menjalankan ulang live tests membutuhkan dependency lokal yang siap dan volume/DB terisolasi. Jangan menjalankan semua tes pada data live hanya dengan mengganti cwd.

Scratch merah/hijau: C:\Users\dmaza\.codex\worktrees\pc-final-verification\mcp-starter\.tmp-recon-audit\regression-remediation. publication-red.log, publication-green.log, topk-red.log, topk-green.log, physical-pages-green.log, ui-layout-red.log, ui-layout-green.log. workflow-definition-red.log dan workflow-green.log/JUnit ada di .tmp-build/pc-stabilization-20261123. Preimage source/test disimpan di scratch; Git diff dari 29e71a81 menunjukkan perubahan tugas.

operation-transcripts/ berisi salinan inert skrip operasi sebagai teks untuk audit, bukan CLI aplikasi yang dijamin portable. Source PDF/model/config rahasia tidak disertakan dalam Git; clean-clone reproduction belum PASS. Manifest backup per file tetap privat pada folder E yang dicatat di BACKUP_BUNDLE_BINDING.json. Prosedur restore hanya ke lokasi baru: database ke knowledge/, source-documents berdampingan di knowledge/source-documents, konfigurasi ke lokasi uji terpisah; verifikasi hash dan integrity sebelum boot. Jangan restore ke lokasi aktif tanpa checkpoint/approval yang sesuai.
