"""Generate Golden Set (Tier A/B/C) for a SOP."""
import sys, json, os

def generate(sop_data, output_path):
    questions = []
    # Tier A: 15-20 questions
    tier_a = [
        {'id': 'G-01', 'q': 'Apa persyaratan %s?' % sop_data.get('title',''), 'answer': 'Lihat bagian E persyaratan.', 'type': 'requirements'},
        {'id': 'G-02', 'q': 'Bagaimana prosedur %s?' % sop_data.get('title',''), 'answer': 'Lihat bagian F prosedur.', 'type': 'procedure'},
        {'id': 'G-03', 'q': 'Berapa lama proses %s?' % sop_data.get('title',''), 'answer': 'Lihat bagian G waktu.', 'type': 'time'},
        {'id': 'G-04', 'q': 'Berapa biaya %s?' % sop_data.get('title',''), 'answer': 'Lihat bagian G biaya.', 'type': 'cost'},
        {'id': 'G-05', 'q': 'Apa dasar hukum %s?' % sop_data.get('title',''), 'answer': 'Lihat bagian C dasar hukum.', 'type': 'legal'},
    ]
    # Tier B: 8-10 questions
    tier_b = [
        {'id': 'G-06', 'q': 'syarat %s' % sop_data.get('title','').lower(), 'answer': 'Typo/bahasa sehari-hari.', 'type': 'typo'},
        {'id': 'G-07', 'q': 'kondisi khusus %s' % sop_data.get('title',''), 'answer': 'Lihat bagian H.', 'type': 'special'},
    ]
    # Tier C: 5 questions
    tier_c = [
        {'id': 'G-08', 'q': 'Cuaca hari ini?', 'answer': 'Ditolak; di luar SOP.', 'type': 'out_of_scope'},
    ]
    golden = {'sop_id': sop_data.get('id_sop',''), 'title': sop_data.get('title',''),
              'tier_a': tier_a, 'tier_b': tier_b, 'tier_c': tier_c}
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    json.dump(golden, open(output_path,'w',encoding='utf-8'), indent=2, ensure_ascii=False)
    print('Golden set saved:', output_path)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: generate_golden_set.py <sop_json> <output_json>')
        sys.exit(1)
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    generate(data, sys.argv[2])
