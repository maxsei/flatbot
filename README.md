# Pynal Smash  
  
  
## Abstract  
Create a model using tensorflow whose behavior in the game Super Smash Brothers  
is emergent.  This means that the model only knows how to press buttons as well  
as other game properties that the player would know such as locations, percent,  
stocks, etc.  All data will be retreived from the game using the memory watcher  
functionality built into dolphin and all inputs will be done through a unix pipe  
functionality also built into dolphin.  
  
## Notes  
* Dolphin [makepkg] 5.0-7309 is the version I am using  
* Much of the data is typed hex values  
* data is comprized of memory locations with offsets that point to more  
  specific data i.e. player block address plus some offset could give you the  
  players stock count or x position  
* frames terminate each transmission of data?  
* I am having issue with the C stick and Dolphin so the bot does not use the C  
  stick for now  
  
## Things I Use Directly  
[installed dolphin from here on the aur](https://www.archlinux.org/packages/community/x86_64/dolphin-emu/)  
[watching game memory locations](https://github.com/dolphin-emu/dolphin/pull/3403)  
[gregstoll float to hex converter](https://gregstoll.com/~gregstoll/floattohex/)  
  
## Inspired By  
[meleelib](https://github.com/altf4/libmelee)  
[phillip AI](https://github.com/vladfi1/phillip)  
[SmashBot](https://github.com/altf4/SmashBot)  
[p3 ssbm ai interface for dolphin](https://github.com/spxtr/p3)  
