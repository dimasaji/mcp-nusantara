from __future__ import annotations


INTENT_PROTOTYPES: dict[str, list[str]] = {

    "ask_document_status": [
        "Saya mau cek status KTP saya",
        "Bagaimana cara mengecek status dokumen saya?",
        "KTP saya sudah selesai belum?",
        "Saya ingin mengetahui status pengajuan KTP",
        "Bagaimana status KTP saya?",
        "Saya mau melihat status dokumen kependudukan",
        "Apakah KTP saya sudah jadi?",
    ],

    "report_missing_document": [
        "Dokumen saya belum diterima",
        "KTP saya belum sampai",
        "Dokumen saya hilang",
        "Saya belum menerima dokumen saya",
        "Dokumen kependudukan saya belum ada",
        "KTP saya belum saya terima",
    ],

    "request_document_issuance": [
        "Saya ingin membuat KTP",
        "Bagaimana cara membuat dokumen kependudukan?",
        "Saya mau mengurus KTP",
        "Saya ingin mengajukan dokumen",
        "Bagaimana cara membuat KK?",
        "Saya mau membuat akta kelahiran",
    ],

    "ask_document_requirements": [
        "Apa saja syarat membuat KTP?",
        "Persyaratan membuat KK apa saja?",
        "Dokumen apa yang harus saya siapkan?",
        "Apa syarat pengurusan dokumen?",
        "Persyaratan membuat akta kelahiran",
        "Apa saja berkas yang diperlukan?",
    ],

    "report_technical_issue": [
        "Aplikasi tidak bisa dibuka",
        "Saya tidak bisa login",
        "Aplikasi error",
        "Website tidak bisa diakses",
        "Saya mengalami masalah pada aplikasi",
        "Sistem sedang error",
        "Aplikasi tidak berjalan",
    ],

    "request_technical_help": [
        "Bagaimana cara menggunakan aplikasi?",
        "Tolong bantu saya menggunakan aplikasi",
        "Saya tidak tahu cara menggunakan fitur ini",
        "Bagaimana cara login?",
        "Bagaimana cara mengupload dokumen?",
        "Cara menggunakan aplikasi bagaimana?",
    ],

    "ask_general_info": [
        "Saya ingin mendapatkan informasi",
        "Tolong berikan informasi",
        "Saya ingin bertanya",
        "Bisa memberikan informasi?",
        "Saya ingin mengetahui informasi layanan",
    ],

    "confirm_action": [
        "Ya",
        "Iya",
        "Benar",
        "Betul",
        "Saya setuju",
        "Lanjutkan",
        "Ya silakan lanjut",
    ],

    "cancel_or_stop": [
        "Tidak jadi",
        "Batalkan",
        "Saya ingin membatalkan",
        "Jangan lanjutkan",
        "Stop",
        "Berhenti",
        "Tidak usah",
    ],

    "greeting": [
        "Halo",
        "Hai",
        "Selamat pagi",
        "Selamat siang",
        "Selamat sore",
        "Selamat malam",
    ],

    "thank_you": [
        "Terima kasih",
        "Makasih",
        "Terima kasih banyak",
        "Saya berterima kasih",
    ],

    "goodbye": [
        "Sampai jumpa",
        "Selamat tinggal",
        "Dadah",
        "Saya pamit",
        "Sampai nanti",
    ],
}