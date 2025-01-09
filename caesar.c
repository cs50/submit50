#include <iostream>
#include <string>
using namespace std;

int main() {
    string name;
    int shifting_number;
    cout << " Shifting number ";
    cin >> shifting_number;

    cin.ignore();

    cout << "Enter your name" << endl;
    getline(cin, name);
for(int i = 0; i < name.length(); i++) {

        if (char(name[i]) == ' ') {
            cout << " ";
        }
else if (name[i] < 'A' || (name[i] > 'Z' && name[i] < 'a') || name[i] > 'z') {
            cout << name[i];
        }
        else if (name[i] >= 'A' && name[i] <= 'Z') {

            cout << char((name[i] - 'A' + shifting_number) % 26 + 'A');
        }
        else if (name[i] >= 'a' && name[i] <= 'z') {

            cout << char((name[i] - 'a' + shifting_number) % 26 + 'a');
        }
    }
    return 0;
}
