import unittest
from unittest.mock import patch, MagicMock
from facefusion.ffmpeg import restore_audio

def test_restore_audio():
    # Mocking state_manager to return specific values
    mock_state_manager.get_item.side_effect = lambda key: {
        'trim_frame_start': 5,
        'trim_frame_end': 20,
        'output_audio_encoder': 'aac'
    }.get(key)

    # Setting the output audio encoder
    mock_state_manager.set_item('output_audio_encoder', 'aac')  # {{ edit_1 }}

    # Mocking get_temp_file_path to return a fake temp file path
    mock_get_temp_file_path.return_value = '/fake/temp/path.mp4'    

    # Mocking run_ffmpeg to return a mock process with a return code of 0 (success)
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_run_ffmpeg.return_value = mock_process

    # Test inputs
    target_path = '/fake/input/path.mp4'
    output_path = '/fake/output/path.mp4'
    output_video_fps = 30.0

    # Call the function
    result = restore_audio(target_path, output_path, output_video_fps)

    # Assertions
    self.assertTrue(result)
    mock_get_temp_file_path.assert_called_once_with(target_path)
    mock_state_manager.get_item.assert_any_call('trim_frame_start')
    mock_state_manager.get_item.assert_any_call('trim_frame_end')
    mock_state_manager.get_item.assert_any_call('output_audio_encoder')

    # Check if run_ffmpeg was called with the correct command
    expected_command = ['-i', '/fake/temp/path.mp4', '-ss', '0.16666666666666666', '-to', '0.6666666666666666', '-i', target_path, '-c:v', 'copy', '-c:a', 'aac', '-ar', '48000', '-map', '0:v:0', '-map', '1:a:0', '-shortest', '-y', output_path]
    mock_run_ffmpeg.assert_called_once_with(expected_command)

# 新しい統合テストメソッドを追加
def test_restore_audio_integration():
    # 実際の入力と出力のパスを定義
    target_path = '/path/to/real/input.mp4'  # 実際の入力ファイルに更新
    output_path = '/path/to/real/output.mp4'  # 出力ファイルの希望に更新
    output_video_fps = 30.0

    # 関数を呼び出す
    result = restore_audio(target_path, output_path, output_video_fps)

    # アサーション
    assert result

# CLIベースのユニットテストメソッドを追加
def test_restore_audio_cli_unit():
    import subprocess

    # テスト用の入力と出力のパスを定義
    target_path = '/fake/input/path.mp4'  # テスト用の入力ファイル
    output_path = '/fake/output/path.mp4'  # テスト用の出力ファイル
    output_video_fps = 30.0

    # CLIコマンドを実行
    command = ['python', 'path/to/your_script.py', target_path, output_path, str(output_video_fps)]
    result = subprocess.run(command, capture_output=True)

    # アサーション
    assert result.returncode == 0  # 成功を確認
    # 追加のアサーションを行うことも可能

if __name__ == '__main__':
    unittest.main()
