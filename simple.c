void exec(){
    string c1 = "hello ";
    string c2 = "world";
    printf(c1+c2);
    printf(len(c1));
    int i = len(c1)-1;
    while(i){
        printf(c1[len(c1)-i-1]);
        i = i-1
    }

}
