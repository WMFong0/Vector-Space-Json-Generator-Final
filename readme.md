# How to get input.txt

- **First, switch to the folder directory**
    - **Windows**

      ![alt text](https://github.com/user-attachments/assets/92fb9056-493c-4c84-9e55-42d62c07b08f)

    - **MacBook**
        - Use cd, e.g.
```
cd "Your document folder path"
```
- **Then**
```
ls -1 > input2.txt
```

## if it returns error, try
    ls | Select-Object -ExpandProperty Name > input2.txt
If lower command were used, go insides input2.txt and remove the line "input2.txt" from the file.

Then Kindly move input.txt from other folder directory to the program directory

output.txt and output2.txt is not nessarily to exist before program execution. The program will automatically create it after program execution (For File input)