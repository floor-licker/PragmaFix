Some noteworthy 
1. If a range is stated, for example `>=0.6.23 <=0.8.0` it's assumed that backwards compatibility is desired, and the script will not update the pragma line to Solidity ^0.8.0
2. If a range is specified where the floor is greater than or equal to 0.8.0, the pragma line will be left as is
3. If the pragma line is currently set to >=0.8.0, it will be left as is
4. If the pragma line simply states an outdated version, it will be updated to ^0.8.0, and any safeMath redundancies will be refactored
