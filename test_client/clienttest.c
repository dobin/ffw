/*
    C ECHO client example using sockets
*/

// http://www.binarytides.com/server-client-example-c-sockets-linux/

#include<stdio.h> //printf
#include<string.h>    //strlen
#include<sys/socket.h>    //socket
#include<arpa/inet.h> //inet_addr
#include <stdlib.h>
#include <unistd.h>

void communicate(int socket) {
    char buf[16];
    int ret;

    ret = send(socket, "hoi", 3, 0);
    if (ret < 0) {
        puts("Send failed");
        return;
    }

    ret = recv(socket, buf, 1024, 0);
    if(ret  < 0) {
       puts("recv failed");
       return;
    }
}

int main(int argc , char *argv[])
{
    int sock;
    struct sockaddr_in server;

    if (argc != 2) {
	printf("Gife port\n");
    }
    int port = atoi(argv[1]);

    //Create socket
    sock = socket(AF_INET , SOCK_STREAM , 0);
    if (sock == -1)
    {
        printf("Could not create socket");
    }
    puts("Socket created");

    server.sin_addr.s_addr = inet_addr("127.0.0.1");
    server.sin_family = AF_INET;
    server.sin_port = htons( port );

    //Connect to remote server
    if (connect(sock , (struct sockaddr *)&server , sizeof(server)) < 0)
    {
        perror("connect failed. Error");
        return 1;
    }

    puts("Connected\n");

    communicate(sock);

    close(sock);
    return 0;
}
