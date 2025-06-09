void add(int b){
    int c = b;
    if (c){
        add1(b)
    }
}

void add1(int b){
    X = X + 1;
    add(b - 1)
}

int X, int Y

void exec(){
    string c1 = "Hello ";
    string c2 = "World";
    printf(c1 + c2);
    add(Y);
    printf(X)
}