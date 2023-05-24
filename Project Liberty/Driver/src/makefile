
all: liberty

liberty: liberty.c liberty.h protocol.h main.c
	gcc -Wall -g -o liberty liberty.c main.c -lusb -ljson-c
	#gcc -g -DDEBUG -o liberty liberty.c main.c -lusb -ljson-c

clean:
	-rm -f liberty *~ 2>/dev/null



