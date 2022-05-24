import 'package:firebase_auth/firebase_auth.dart';
import 'package:rxdart/rxdart.dart';

class XRPegProductionFirebaseUser {
  XRPegProductionFirebaseUser(this.user);
  User user;
  bool get loggedIn => user != null;
}

XRPegProductionFirebaseUser currentUser;
bool get loggedIn => currentUser?.loggedIn ?? false;
Stream<XRPegProductionFirebaseUser> xRPegProductionFirebaseUserStream() =>
    FirebaseAuth.instance
        .authStateChanges()
        .debounce((user) => user == null && !loggedIn
            ? TimerStream(true, const Duration(seconds: 1))
            : Stream.value(user))
        .map<XRPegProductionFirebaseUser>(
            (user) => currentUser = XRPegProductionFirebaseUser(user));
