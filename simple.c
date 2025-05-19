funct add(a,b){
    if(b){
        a = a + 1 ;
        b = b - 1 ;
        return (add(a,b)) 
    }else{
        return (a)
    }
}

X, Y

funct main(){
    return (add(X,Y))
}
