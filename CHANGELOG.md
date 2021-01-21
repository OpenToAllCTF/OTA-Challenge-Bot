# Changelog
All notable changes to this project will be kept in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [1.1.0] - 2021-01-20
### Added
* Pulled in features developed for Samurai!
* Ability to create private CTFs (b1e9456)
* Ability to auto-invite all CTF channel members to new challenges(1a087b1)
* Ability to archive only challenges (fff0bda)
* !signup (566b39b)
* !populate (!gather, !summon) (8a7d77d)
* !join (c0f2db9)
* !makectf (cec0d3e)
* !debug (3f7730f)
* get_channel_by_name() (4a36d1d)

### Changed
* Update AddCTFCommand to handle results of call to conversations API. (b1e9456)
* Switch set_purpose from events to conversations API. (a6048e7)
* Implement the conversations API for listing channels. (4a36d1d)
* Update get_channel_members() to use new slack API. (3c8d707)
* Update !archivectf to use new slack API. (c241342)
* Miscellaneous:
* Make category optional when adding challenge (5fc6468)
* Stop set_config_option mangling file indentation (f2394ed)
* Remove player list from status to cut down on noise (c6aebbb)
* Alias !archive and !archivectf (c241342)
* Make !add an alias of !addchallenge (3ff51e7)

## [1.0.0] - 2021-01-18
"Stable" - The development version we've been using for > 6 months. With the
[deprecation of the
API](https://api.slack.com/changelog/2020-01-deprecating-antecedents-to-the-conversations-api)
we need to port everything over to the new conversations API. Cutting this
release for posterity.

## [0.1.0] - 2019-09-10
Initial release
