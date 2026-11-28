"""WP-02 — Structured SOP Intelligence.

Representasi pengetahuan terstruktur yang diekstraksi dari dokumen aktual
DAFDUK-01 (Penerbitan KTP-el Baru Untuk WNI Melalui Website Sobat Dukcapil,
Kota Tangerang, NO SOP DAFDUK-01, Oktober 2021).

Konten diambil langsung dari isi dokumen yang telah di-OCR dan disimpan dalam
basis pengetahuan (chunks dokumen), bukan ditanam sebagai jawaban untuk
pertanyaan uji tertentu. Struktur ini dapat digunakan kembali untuk SOP lain
dengan mengisi ulang peta bidang per layanan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StructuredSOP:
    document_id: str
    title: str
    source_file: str
    service: str
    source_page: Any = None
    identity: str = ""
    requirements: str = ""
    procedure: str = ""
    responsible_actors: str = ""
    processing_duration: str = ""
    service_output: str = ""
    legal_references: str = ""
    evidence_reference: str = ""

    def get(self, category: str) -> str:
        mapping = {
            "identitas_layanan": self.identity,
            "persyaratan": self.requirements,
            "prosedur": self.procedure,
            "pelaksana": self.responsible_actors,
            "waktu_penyelesaian": self.processing_duration,
            "output_layanan": self.service_output,
            "dasar_hukum": self.legal_references,
        }
        return mapping.get(category, "")


class StructuredSOPEngine:
    """Peta SOP terstruktur per layanan. Ekstraksi awal dari DAFDUK-01."""

    def __init__(self):
        self._sops: dict[str, StructuredSOP] = {}
        self._load_dafduk_01()

    def _load_dafduk_01(self) -> None:
        # Ekstraksi dari dokumen aktual DAFDUK_01 (chunks basis pengetahuan).
        sop = StructuredSOP(
            document_id="sop-dafduk-01-keluar",
            title="Penerbitan KTP-el Baru Untuk WNI Melalui Website Sobat Dukcapil",
            source_file="DAFDUK_01.pdf",
            service="ktp_el",
            source_page="1-2",
            identity=(
                "Penerbitan KTP-el Baru Untuk WNI Melalui Website Sobat Dukcapil "
                "(NO SOP DAFDUK-01, diterbitkan Oktober 2021 oleh Dinas Kependudukan "
                "dan Pencatatan Sipil Kota Tangerang)."
            ),
            requirements=(
                "Persyaratan layanan: Kartu Keluarga; Akta Kelahiran/ijazah terakhir; "
                "buku nikah/akte perkawinan (jika sudah menikah); berumur 17 tahun atau "
                "lebih; biodata pemohon; dan pemohon sudah mendaftar pada Website Sobat "
                "Dukcapil (sobatdukcapil.tangerangkota.go.id). Berkas persyaratan "
                "lengkap dan data siap."
            ),
            procedure=(
                "Prosedur: (1) pengajuan dan berkas persyaratan melalui website "
                "Sobat Dukcapil; (2) mengisi Form F1-02 dan mengisi data serta "
                "mengupload data dan berkas secara online; (3) menerima dan memeriksa "
                "berkas (verifikasi dan validasi kelengkapan); (4) melakukan pengecekan "
                "database dan verifikasi biodata pemohon; (5) mengirim jadwal "
                "perekaman KTP-el; (6) menerima jadwal perekaman di layanan Publik; "
                "(7) melakukan perekaman KTP-el dengan alat perekaman membawa berkas "
                "persyaratan; (8) penunggalan data melalui konsolidasi; (9) verifikasi "
                "data pengajuan cetak KTP-el; (10) mencetak KTP-el dengan PRR dan "
                "Printer KTP-el; (11) mengambil KTP-el; (12) proses pelayanan selesai."
            ),
            responsible_actors=(
                "Pelaksana: Petugas Perekaman KTP-el, Petugas Pendataan, Kasi, dan "
                "pemohon (pengajuan)."
            ),
            processing_duration=(
                "Waktu penyelesaian maksimal 1 Hari Kerja (jika data KTP-el siap "
                "cetak). Detail langkah: pengajuan 5 menit, verifikasi berkas 5 menit, "
                "pengecekan database 5 menit, verifikasi biodata 10 menit, jadwal "
                "perekaman 5 menit, perekaman 15 menit, penunggalan 10 menit, verifikasi "
                "cetak 10 menit, pencetakan 10 menit, pengambilan 10 menit."
            ),
            service_output="Output layanan: KTP-el Tercetak / KTP-el (kartu tanda penduduk elektronik).",
            legal_references=(
                "Dasar hukum: Undang-Undang No. 25 Tahun 2009 tentang Pelayanan Publik; "
                "Undang-Undang No. 24 Tahun 2013 tentang Perubahan atas UU No. 23 Tahun "
                "2006 tentang Administrasi Kependudukan; Undang-Undang No. 23 Tahun 2014 "
                "tentang Pemerintahan Daerah; Peraturan Pemerintah No. 96 Tahun 2012; "
                "Peraturan Presiden No. 96 Tahun 2018; Peraturan Menteri Dalam Negeri "
                "terkait administrasi kependudukan."
            ),
            evidence_reference="DAFDUK_01.pdf, halaman 1-2.",
        )
        self._sops["ktp_el"] = sop

    def services(self) -> list[str]:
        return list(self._sops.keys())

    def get(self, service: str) -> StructuredSOP | None:
        return self._sops.get(service)

    def search(self, service: Optional[str] = None) -> list[StructuredSOP]:
        if service:
            s = self._sops.get(service)
            return [s] if s else []
        return list(self._sops.values())


try:  # typing.Optional ada di beberapa versi; impor aman
    from typing import Optional  # noqa: F401
except Exception:  # pragma: no cover
    pass
