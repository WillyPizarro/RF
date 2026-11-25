# google_mlkit_text_recognition 1.0.3 declara como compileOnly los reconocedores de otros
# alfabetos (chino, devanagari, japonés y coreano). La app solo usa el latino
# (TextRecognitionScript.latin), así que esas clases no van en el APK y R8 no debe exigirlas.
-dontwarn com.google.mlkit.vision.text.chinese.**
-dontwarn com.google.mlkit.vision.text.devanagari.**
-dontwarn com.google.mlkit.vision.text.japanese.**
-dontwarn com.google.mlkit.vision.text.korean.**

# ok_http 0.1.0 (CONTRATO-MIGRACION-FLUTTER v1.5 §6) llama a OkHttp, Okio y a sus propias clases
# Kotlin desde Dart por JNI, buscándolas por nombre. R8 no ve esas llamadas: sin estas reglas,
# renombra o quita las clases y el APK de release no encuentra `okhttp3/OkHttpClient` al arrancar.
-keep class okhttp3.** { *; }
-keep class okio.** { *; }
-keep class com.example.ok_http.** { *; }
