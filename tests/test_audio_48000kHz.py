import unittest
from unittest.mock import patch, MagicMock
from facefusion.ffmpeg import restore_audio

class TestRestoreAudio(unittest.TestCase):

    @patch('facefusion.ffmpeg.state_manager')
    @patch('facefusion.ffmpeg.get_temp_file_path')
    @patch('facefusion.ffmpeg.run_ffmpeg')
    def test_restore_audio(self, mock_run_ffmpeg, mock_get_temp_file_path, mock_state_manager):
        # Mocking state_manager to return specific values
        mock_state_manager.get_item.side_effect = lambda key: {
            'trim_frame_start': 5,
            'trim_frame_end': 20,
            'output_audio_encoder': 'aac'
        }.get(key)

        # この行を追加して output_audio_encoder を設定
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
        expected_command = [
            '-i', '/fake/temp/path.mp4',
            '-ss', '0.16666666666666666',  # 5 / 30.0
            '-to', '0.6666666666666666',   # 20 / 30.0
            '-i', target_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-ar', '48000',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            '-y', output_path
        ]
        mock_run_ffmpeg.assert_called_once_with(expected_command)

if __name__ == '__main__':
    unittest.main()
