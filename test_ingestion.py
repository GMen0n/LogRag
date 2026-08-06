import os
from ingestion import OpenStackLogIngestor

# Sample log data provided in your dataset snippet for immediate local testing
SAMPLE_DATASET = """
nova-api.log.1.2017-05-16_13:53:08 2017-05-16 00:00:00.008 25746 INFO nova.osapi_compute.wsgi.server [req-38101a0b-2096-447d-96ea-a692162415ae 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2477829
nova-compute.log.1.2017-05-16_13:55:31 2017-05-16 00:00:04.500 2931 INFO nova.compute.manager [req-3ea4052c-895d-4b64-9e2d-04d64c4d94ab - - - - -] [instance: b9000564-fe1a-409b-b8cc-1e88b294cd1d] VM Started (Lifecycle Event)
nova-compute.log.1.2017-05-16_13:55:31 2017-05-16 00:00:20.345 2931 WARNING nova.virt.libvirt.imagecache [req-addc1839-2ed5-4778-b57e-5854eb7b8b09 - - - - -] Unknown base file: /var/lib/nova/instances/_base/a489c868f0c37da93b76227c91bb03908ac0e742
"""

def test_string_ingestion():
    print("🧪 Running Ingestion Test on Dataset String Buffer...")
    ingestor = OpenStackLogIngestor(chunk_size=50, overlap=10)
    chunks = ingestor.parse_string(SAMPLE_DATASET)

    assert len(chunks) > 0, "Failed to generate chunks from sample string!"
    print(f"✅ String Parsing Successful! Generated {len(chunks)} chunk(s).")
    print(f"🔹 Sample Chunk 0:\n{chunks[0]['text']}\n")

def test_file_ingestion(log_file_path: str):
    print(f"🚀 Running Ingestion Test on Log File: {log_file_path}...")
    ingestor = OpenStackLogIngestor(chunk_size=300, overlap=50)

    if not os.path.exists(log_file_path):
        print(f"⚠️ Warning: File '{log_file_path}' not found locally. Skipping file test.")
        return

    chunks = ingestor.parse_file(log_file_path)
    print("✅ File Ingestion Successful!")
    print(f"📊 Total Chunks Generated: {len(chunks)}")
    
    if chunks:
        print("\n--- CHUNK 0 PREVIEW ---")
        print(f"ID: {chunks[0]['chunk_id']}")
        print(f"Metadata: {chunks[0]['metadata']}")
        print(f"Snippet: {chunks[0]['text'][:250]}...")
        print("-----------------------")

if __name__ == "__main__":
    # Test 1: In-memory string snippet verification
    test_string_ingestion()
    test_file_ingestion("loghub-master-dataset/OpenStack/OpenStack_2k.log")