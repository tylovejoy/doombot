# Changelog

<!--next-version-placeholder-->

## v2.3.0 (2021-07-18)
### Feature
* Added guide support ([`3d1be88`](https://github.com/tylovejoy/doombot/commit/3d1be880c98c0fb36bd34cd5a51502c07163fe53))
* Added select menu to most tournament.py commands. ([`f273762`](https://github.com/tylovejoy/doombot/commit/f273762a9a5d9e9ccbb6478c0cbe7ddcc8f964cc))
* Added TournamentChoices view. Implemented in lock command ([`cf88123`](https://github.com/tylovejoy/doombot/commit/cf881233d3f490da4fc9c827555cbc0dd1546962))

### Fix
* Imports ([`80698ea`](https://github.com/tylovejoy/doombot/commit/80698ea7f0e4f86b0753c45f583f61aa75db5b5a))
* Removed reference code for errors ([`2674243`](https://github.com/tylovejoy/doombot/commit/2674243bcd08c91b287a440d18d3d0cecf31873b))
* Corrected editcreator help message ([`9aa5580`](https://github.com/tylovejoy/doombot/commit/9aa5580b3a5e12a69c2a861836a7a00ffc26d7df))
* Corrected embed footer being set on the wrong object ([`5f3d5c0`](https://github.com/tylovejoy/doombot/commit/5f3d5c0127baf5676d98e51109f67fdb86f50a9d))
* Correct custom emoji ([`9bc44e0`](https://github.com/tylovejoy/doombot/commit/9bc44e06a7dcee85c90b649d7412016683530b77))
* Unnecessary clear_items() ([`95f2a80`](https://github.com/tylovejoy/doombot/commit/95f2a80eb0c144b22ffa3fca2a02cfd0308272ec))

## v2.2.0 (2021-07-18)
### Feature
* Add semantic-release to pyproject.toml and add CHANGEGLOG.md ([`02cba22`](https://github.com/tylovejoy/doombot/commit/02cba2264f5187429b634eb4de432a65fe748464))
* Error_handler.py added ([`447831e`](https://github.com/tylovejoy/doombot/commit/447831e5d92ec946ee4d263fbe409da417697dc3))
* Added tournament support ([`8a2f7ba`](https://github.com/tylovejoy/doombot/commit/8a2f7ba8ed38ecd2a667b2c6a36055249c8f32b2))
* Incorrect import ([`46b3fb8`](https://github.com/tylovejoy/doombot/commit/46b3fb8a3126373bd50ee0aabad7bb0a6f1a6aba))
* Pretty_help.py implementation ([`5d8168c`](https://github.com/tylovejoy/doombot/commit/5d8168c26640e7ca226aa15cd424c244408e2eff))
* Very cool ascii art on startup ([`0a5d107`](https://github.com/tylovejoy/doombot/commit/0a5d10782a98ae07af0c6e07c46631658df2699d))
* Fixed lingering Embeds->doom_embed conversion ([`524b305`](https://github.com/tylovejoy/doombot/commit/524b305a63a9973101421e86ae9d6aa3b225f1c6))
* Added deletepb ([`18e53b6`](https://github.com/tylovejoy/doombot/commit/18e53b6e402114a41ad3d7da2ac9eaf988b81e41))
* Added map_help.py ([`08fd09d`](https://github.com/tylovejoy/doombot/commit/08fd09d17227aa7a8d92480d17531268a450dfa0))
* Added pb_utils.py and new verification view ([`3dacdb6`](https://github.com/tylovejoy/doombot/commit/3dacdb6fcb5474edda42f229520a2fd3c88dfc42))
* Added map_search_types.py ([`523dae3`](https://github.com/tylovejoy/doombot/commit/523dae3ce80ca505ee626e1c26adfa825c52b625))
* Added basic map_search ([`21d19f0`](https://github.com/tylovejoy/doombot/commit/21d19f05c1a0658ec01304ef932f9ae7e78732bd))
* Refactored confirm.py into views.py ([`0936392`](https://github.com/tylovejoy/doombot/commit/09363923f6d82745fdb6093ff9ec50c7991f6309))
* Added all submit_map.py functions ([`347e9cc`](https://github.com/tylovejoy/doombot/commit/347e9ccd323366935e421084366114a521bdc131))
* Added pre-commit everything ([`852b57b`](https://github.com/tylovejoy/doombot/commit/852b57b755ffffc8ae5f63d565fa914b8bbabcd8))

### Fix
* Import errors fixed ([`0c680a2`](https://github.com/tylovejoy/doombot/commit/0c680a2abeab81a5a47a05e0a72d579fb24792b4))
* Added wizards to requirements.txt ([`97db621`](https://github.com/tylovejoy/doombot/commit/97db6211a79c6fc19f0f706ef76dea17fa1ba47e))
* Added disutils to requirements.txt ([`2166979`](https://github.com/tylovejoy/doombot/commit/21669795ade3389fdde6d20a829393fc888978f3))
* Command usage errors ([`6722144`](https://github.com/tylovejoy/doombot/commit/6722144a89a8cea608981e6d741e25025e9c72aa))
* Fixed requirements.txt ([`90dfa74`](https://github.com/tylovejoy/doombot/commit/90dfa7451c529010d08b744de0f9bc7486253ee7))
* Removed unnecessary comments and lines of code ([`73f239d`](https://github.com/tylovejoy/doombot/commit/73f239de27d33f58bba34de096c189ccb60494be))
* Removed bot.logout() deprecated? ([`e20ad02`](https://github.com/tylovejoy/doombot/commit/e20ad022efe5e6a64cfdf7cd787457432ebcba12))
* Remove on_message listener map_search.py ([`38c3780`](https://github.com/tylovejoy/doombot/commit/38c37804d5cbb8b0156fc69ece948fd66697934e))
* Converted all Embed to doom_embed ([`33ba16b`](https://github.com/tylovejoy/doombot/commit/33ba16b611e719c956421162d820e88f7277d39f))
* Todos ([`82dd435`](https://github.com/tylovejoy/doombot/commit/82dd4355f3bcc23e23a90a05c0f8d512a05e4f79))
* Changed some views ([`3cc72be`](https://github.com/tylovejoy/doombot/commit/3cc72bee7aaf3ba0779bce9d7e2732e6123cb5a0))
* Requirements.txt ([`34b5277`](https://github.com/tylovejoy/doombot/commit/34b52776222c4db787906993a028fe5525a380da))
* Known_third_party ([`b20836a`](https://github.com/tylovejoy/doombot/commit/b20836af3ca959f54d974fe38c97eecfa274c8ca))
