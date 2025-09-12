# Copyright (C) 2023-2025 SIPez LLC.  All rights reserved.
""" FilterPlugin for Deepgram transcription """
import typing
import json
import logging
import pydantic
import requests
import tenacity
import vcon.filter_plugins
import deepgram

logger = vcon.build_logger(__name__)

DEEPGRAM_RETRY_EXCEPTIONS = (requests.exceptions.ReadTimeout)

class DeepgramInitOptions(
  vcon.filter_plugins.FilterPluginInitOptions,
  title = "Deepgram transcription **FilterPlugin** intialization object"
  ):
  """
  A **DeepgramInitOptions** object is provided to the
  **Deepgram FilterPlugin.__init__** method when it is first loaded.  Its
  attributes effect how the registered **FilterPlugin** functions.
  """
  deepgram_key: str = pydantic.Field(
    title = "**Deepgram** API key",
    description = """
The **deepgram_key** is used to access the Deepgram RESTful transcription service.
It is required to use this **FilterPlugin**.

You can get one at: https://console.deepgram.com/signup?jump=keys
""",
    examples = ["123456789e96a1da774e57abcdefghijklmnop"],
    default = ""
    )


class DeepgramOptions(
  vcon.filter_plugins.TranscribeOptions,
  title = "Deepgram transcription filter method options"
  ):
  """
  Options for transcribing the recording **dialog** objects using
  Deepgram transcription service.  The resulting transcription(s)
  are added as transcript **analysis** objects in this **Vcon**

  More details on the OpenAI specific parameters can be found here:
  https://developers.deepgram.com/reference/pre-recorded
  """


class Deepgram(vcon.filter_plugins.FilterPlugin):
  """
  **FilterPlugin** for transcription using **Deepgram**
  """
  init_options_type = DeepgramInitOptions

  def __init__(
    self,
    init_options: DeepgramInitOptions
    ):
    """
    Parameters:
      init_options (DeepgramInitOptions) - the initialization options for the **Deepgram** transcription plugin
    """
    super().__init__(
      init_options,
      DeepgramOptions
      )

    if(init_options.deepgram_key is None or
      init_options.deepgram_key == ""):
      logger.warning("Deepgram plugin: key not set.  Plugin will be a no-op")
      self.deepgram_client = None

    else:
      self.deepgram_client = deepgram.Deepgram(init_options.deepgram_key)




  @tenacity.retry(
      #retry=retry_if_exception_type((openai.error.APIError, openai.error.APIConnectionError, openai.error.RateLimitError, openai.error.ServiceUnavailableError, openai.error.Timeout)), 
      retry = tenacity.retry_if_exception_type(DEEPGRAM_RETRY_EXCEPTIONS),
      wait = tenacity.wait_random_exponential(multiplier = 1, max = 90),
      stop = tenacity.stop_after_attempt(16),
      before = tenacity.before_log(logger, logging.DEBUG),
      after = tenacity.after_log(logger, logging.DEBUG)
    )
  def request_transcribe(
    self,
    recording_data: typing.Dict[str, typing.Any],
    transcribe_options: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
    """ synchronous post of deepgram transcrtion request """
    url = "https://api.deepgram.com/v1/listen"
    headers = {
      "accept": "application/json",
      "content-type": recording_data["mediatype"],
      "Authorization": "Token " + self._init_options.deepgram_key
      }
    # Should make this a parameter
    requests_options = {
      "timeout": 200
      }

    response = requests.post(
      url,
      params = transcribe_options,
      #json = recording_data,
      data = recording_data["buffer"],
      headers = headers,
      **requests_options
      )

    if(response.status_code >= 300):
      logger.warning("request to: {} with {} failed: {}: {}".format(
        url,
        transcribe_options,
        response.status_code,
        response.content
        ))
      raise Exception("request to Deepgram options: {} failed: {}".format(
        transcribe_options,
        response.status_code
        ))

    return(json.loads(response.content))


  async def filter(
    self,
    in_vcon: vcon.Vcon,
    options: DeepgramOptions
    ) -> vcon.Vcon:
    """
    Transcribe the recording dialog objects using **Deepgram**.

    Parameters:
      options (DeepgramOptions)

    Returns:
      the modified Vcon with added transcript analysis objects for the recording dialogs.
    """
    out_vcon = in_vcon

    if(in_vcon.dialog is None):
      return(out_vcon)

    dialog_indices = self.slice_indices(
      options.input_dialogs,
      len(in_vcon.dialog),
      "DeepgramOptions.input_dialogs"
      )

    # no dialogs
    if(len(dialog_indices) == 0):
      return(out_vcon)

    if(self.deepgram_client is None):
      logger.warning("Deepgram.filter: deepgram_key is not set, no transcription performed")
      return(out_vcon)

    analysis_extras = {
      "product": "transcription"
      }

    # TODO add some of these to DeepgramOptions
    transcribe_options = {
      'language': 'en',
      'model': 'nova-3',  # should make this an option: nova-2, nova-2-phonecall, nova-2-meeting, nova-2-medical
      'punctuate': 'true',
      'smart_format': 'true',
      'diarize': 'true'
      }

    for dialog_index in dialog_indices:
      dialog = in_vcon.dialog[dialog_index]
      if(dialog["type"] == "recording"):
        transcript_index = in_vcon.find_transcript_for_dialog(
          dialog_index,
          True,
          [
            ("deepgram", "transcription", "deepgram_prerecorded")
          ]
          )

        # We have not already transcribed this dialog
        if(transcript_index is None):
          recording_bytes = await in_vcon.get_dialog_body(dialog_index)
          logger.debug("deepgram mediatype: {}".format(dialog['mediatype']))
          if(dialog["mediatype"] == vcon.Vcon.MEDIATYPE_AUDIO_WAV):
            # wave does not support all codecs (e.g. GSM)
            #with wave.open(io.BytesIO(recording_bytes), "rb") as wave_file:
            #  codec_type = wave_file.getcomptype()
            #  codec_name = wave_file.getcompname()
            #  logger.info("deepgram transcribe of wav codec type: {} name: {}".format(codec_type, codec_name))

            # the following does not takes a stream or bytes array despite what the AI says
            # with io.BytesIO(recording_bytes) as recording_io:
            #   audio_info = pydub.utils.mediainfo(bytes(recording_bytes, 'utf-8'))
            #   logger.info("wav file info: {}".format(audio_info))

            # So hack it:
            #  Wav Header should look like this:
            # "RIFFllllWAVEfmt ffffccCCssaa..."
            # llll - length
            # ffff - frame size
            # cc - codec ID
            # CC - channel count
            file_type = recording_bytes[:4]
            format_type = recording_bytes[8:12]
            format_label = recording_bytes[12:16]
            codec_frame_size_bytes = recording_bytes[16:18]
            codec_bytes =  recording_bytes[18:20]
            codec_channeld_bytes = recording_bytes[20:22]
            if(file_type != b'RIFF' or
                format_type != b'WAVE' or
                format_label != b'fmt '
              ):
              logger.warning("Wav file header not as expected.  file type: '{}' format: '{}' format label: '{}'".format(
                file_type, format_type, format_label))

          recording_data = {
            "buffer": recording_bytes,
            "mediatype": dialog["mediatype"]
            }

          transcript_dict = self.request_transcribe(
            recording_data,
            transcribe_options
            )

          # For now make synch.
          # transcript_dict = await self.deepgram_client.transcription.prerecorded(
          #   recording_data,
          #   transcribe_options
          #   )
          # logger.debug("deepgram return type: {} value: {}".format(type(transcript_dict), transcript_dict))
          out_vcon.add_analysis_transcript(
            dialog_index,
            transcript_dict,
            "deepgram",
            "deepgram_prerecorded",
            **analysis_extras
            )

    return(out_vcon)

