# Copyright (C) 2023-2025 SIPez LLC.  All rights reserved.
"""
Unit test for migration of vCon versions
"""

import vcon
import vcon.security

def test_migrate_0_0_1():
  vcon_json = vcon.security.load_string_from_file("tests/pre_0.0.1_vcon_trans.vcon")

  migrated_vcon = vcon.Vcon()
  migrated_vcon.loads(vcon_json)

  assert("body" in migrated_vcon.analysis[0])
  assert("transcript" not in migrated_vcon.analysis[0])
  assert("encoding" in migrated_vcon.analysis[0])
  assert(migrated_vcon.analysis[0]["encoding"] == "json")
  assert(migrated_vcon.analysis[0]["body"]['a'] == "b")
  assert(migrated_vcon.analysis[0]["body"]['c'] == 3)

  # Should be converted to RFC3339 format date
  assert(migrated_vcon.dialog[0]['start'] == "2022-05-18T23:05:05.000+00:00")


def test_migrate_0_0_2():
  vcon_json = vcon.security.load_string_from_file("tests/ab_call_ext_rec_0.0.1.vcon")

  migrated_vcon = vcon.Vcon()
  migrated_vcon.loads(vcon_json)

  assert("mimetype" not in migrated_vcon.dialog[0])
  assert(migrated_vcon.dialog[0]["mediatype"] == "audio/x-wav")

  assert("signature" not in migrated_vcon.dialog[0])
  assert("alg" not in migrated_vcon.dialog[0])
  assert(migrated_vcon.dialog[0]["content_hash"] == "sha512-Re9R7UWKaD7yN9kxoYLbFFNSKU8XfH18NFbTc3AgT4_aBubMtvGUEtRmP6XUxSS3Nl4LU-1mOCtezoTHQ67cVQ")

  assert("mimetype" not in migrated_vcon.analysis[0])
  assert(migrated_vcon.analysis[0]["mediatype"] == "application/foo")
  assert(migrated_vcon.analysis[0]["product"] == "bob")
  assert(migrated_vcon.analysis[0]["schema"] == "bobject")
  assert(migrated_vcon.analysis[0]["encoding"] == "none")

  assert(migrated_vcon.analysis[1]["mediatype"] == "application/foo")
  assert(migrated_vcon.analysis[1]["product"] == "whisper")
  assert(migrated_vcon.analysis[1]["vendor"] == "openai")
  assert(migrated_vcon.analysis[1]["encoding"] == "none")

