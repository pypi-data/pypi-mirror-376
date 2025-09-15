import time
import requests
import json
import tiktoken
from concurrent.futures import ThreadPoolExecutor

# ���ò���
API_URL = "http://gpus.dev.cyberspike.top:8000/v1/chat/completions"
MODEL_NAME = "al-1s-20250421/"
TEST_ROUNDS = 100  # �����ִ�
MAX_WORKERS = 10  # �����߳���

# ����������������ʵ���������ģ�����ƣ�
enc = tiktoken.encoding_for_model("gpt-3.5-turbo")


def generate_complex_prompt():
    """���ɸ��ӵ����簲ȫ���prompt"""
    return """
    ����ϸ�����������簲ȫ������������������
    1. ��⵽���������쳣�ĺ����ƶ���Ϊ�����ͨ������������λ����Դ��
    2. �������ع��CVE-2024-1234©���������Ʒֽ׶εķ������ԣ�
    3. ���������μܹ�����ԭ�������е�ʵʩҪ�㣬���ٰ���5���ؼ����Ƶ�
    4. ���һ������ATT&CK��ܵ������������������Ҫ�����Ԥ����������Ӧ�����׶�
    """.strip()


def count_tokens(text):
    """�����ı���token����"""
    return len(enc.encode(text))


def test_api_call():
    """����API���ò���"""
    prompt = generate_complex_prompt()
    start_time = time.time()

    try:
        response = requests.post(
            API_URL,
            headers={
                "accept": "application/json",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "messages": [{
                    "content": prompt,
                    "role": "user",
                    "name": "user"
                }],
                "model": MODEL_NAME
            }),
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            output_text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            token_count = count_tokens(output_text)
            return {
                'success': True,
                'time': time.time() - start_time,
                'token_count': token_count
            }
        else:
            return {'success': False, 'error': f"HTTP {response.status_code}"}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def main():
    total_time = 0
    total_tokens = 0
    success_count = 0
    failed_count = 0

    print(f"��ʼ���ԣ���{TEST_ROUNDS}�֣���󲢷�{MAX_WORKERS}...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(test_api_call) for _ in range(TEST_ROUNDS)]

        for future in futures:
            result = future.result()
            if result['success']:
                total_time += result['time']
                total_tokens += result['token_count']
                success_count += 1
            else:
                failed_count += 1

    # ����ָ��
    if success_count > 0:
        avg_time_per_call = total_time / success_count
        tokens_per_second = total_tokens / total_time
        rpm = (success_count / total_time) * 60

        print("\n--- ���Խ�� ---")
        print(f"�ɹ�����: {success_count}/{TEST_ROUNDS}")
        print(f"ʧ������: {failed_count}")
        print(f"ƽ����Ӧʱ��: {avg_time_per_call:.2f}��/��")
        print(f"������token��: {total_tokens}")
        print(f"ƽ��token�ٶ�: {tokens_per_second:.2f} tokens/��")
        print(f"������: {rpm:.2f} ��/����")
    else:
        print("���������ʧ�ܣ�����API����״̬")


if __name__ == "__main__":
    main()