# google_mlkit_text_recognition 1.0.3 declara como compileOnly los reconocedores de otros
# alfabetos (chino, devanagari, japonés y coreano). La app solo usa el latino
# (TextRecognitionScript.latin), así que esas clases no van en el APK y R8 no debe exigirlas.
-dontwarn com.google.mlkit.vision.text.chinese.**
-dontwarn com.google.mlkit.vision.text.devanagari.**
-dontwarn com.google.mlkit.vision.text.japanese.**
-dontwarn com.google.mlkit.vision.text.korean.**
