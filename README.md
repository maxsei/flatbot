# Flatbot

## Abstract
Create a model whose behavior in the game Super Smash Brothers is emergent.  The model knows it's available options and the current subset of the game's state.  The model if fed with data from the game by using the memory watcher functionality built into dolphin to listen to updated game states. The modelling strategy is to use a discrete Q learning model as a baseline.  Once the baseline model has converged the next model is to use a deep learning model to approximate the Q table as opposed to updating and sampling a Q table directly.

## General Notes

## Setup
* Uses dolphin 5.0-7309
* data is a list of memory locations with offsets that point to more
	specific data i.e. player block address plus some offset could give you the players stock count or x position

### General Melee Tech
* neutral:
	* dashing
	* jumping
	* [wavedashing/wavelanding](https://www.youtube.com/watch?v=2uSRxDcMiC0)
* offensive options:
	* ground/aerial/smash/special attacks
	* grabs and throws
	* [L-cancelling](https://www.youtube.com/watch?v=ctOYaVrtIgg)
	* [tech chasing](https://www.youtube.com/watch?v=OkMsQGlcrgU)
* defensive options:
	* spot dodge
	* air dodge
	* roll
	* DI (Directional Influence)
	* SDI ([Smash Direction Influence](https://www.youtube.com/watch?v=0g3ka4E17As))
	* [teching](https://www.youtube.com/watch?v=Eo2Lbs-KLRc)
	* [crouch cancelling](https://www.youtube.com/results?search_query=l+cancel+dash+practical+tas)
	* [meteor cancelling](https://www.youtube.com/results?search_query=meteor+cancelling)
* ledge options:
	* normal get up
	* rolling up from the ledge
	* attack from ledge
	* drop from ledge
	* jump from ledge
	* [ledge dash](https://www.youtube.com/watch?v=O0JQeVcpd_g)
* out of sheild options:
	* jump
	* grab
	* roll
	* spot dodge

### Character Aspects
	* fall speed
	* speed
	* range
	* move speed/move power/moveset
	* combo potential offensively and defensively
	* character specific options
	* matchups with other characters

#### Game Aspects
* spacing: how much space there is between two characters and the ranges that
	each character can threaten with their moveset
* stage control: how much real estate does one character have over the other
* percentage: a value that increases when characters damage each other that also
	increases knockback dealt.
* stock count: how many stocks (lives) each character has
* trading potential: is one aspect of the game worth more than another in a
	given situation i.e. is taking damage worth gaining stage positioning
* projectiles: some characters have projectiles to use at their advantage
* frame advantage: does a move take longer to start up or end that one might get
	punished for doing such a move
* grabs: grabs can beat sheilding and can lead mixups with sheilding meta
* Directional Influence: typically characters that are at a lower percentage
	want to DI away from their oppenent to avoid follow up hits and towards their oppenent to survive powerful hits
* hitstun: players that are hit by a move are put into hit stun for a period of
	time where their only actionable option is directional option is teching and Directional Influence
* intangibility frames: there are times when a character is invicible such as on
	getting on and off of the ledge for a brief period
* recoverying: the ability of character to make it back to the stage when hit
	offstage
* edge guarding: the ability to prevent a character off stage from making it
	back to the stage

## Things I Use Directly
[installed dolphin from here on the aur](https://www.archlinux.org/packages/community/x86_64/dolphin-emu/)
[watching game memory locations](https://github.com/dolphin-emu/dolphin/pull/3403)
[gregstoll float to hex converter](https://gregstoll.com/~gregstoll/floattohex/)

## Inspired By
[meleelib](https://github.com/altf4/libmelee)
[phillip AI](https://github.com/vladfi1/phillip)
[SmashBot](https://github.com/altf4/SmashBot)
[p3 ssbm ai interface for dolphin](https://github.com/spxtr/p3)
