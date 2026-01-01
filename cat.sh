cat instructions.txt > combined_prompt.txt
echo "\n\nHere is the data file messages_processed.json:\n" >> combined_prompt.txt
cat messages_processed.json >> combined_prompt.txt
