import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';

/// Profile: account, farm → field → device chain, and honest settings —
/// backend URL, demo/live switch. No secrets ever live here.
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final cfg = ref.watch(appConfigProvider);
    final urlCtrl = TextEditingController(text: cfg.baseUrl);

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: ListTile(
              leading: const CircleAvatar(child: Icon(Icons.person)),
              title: Text(auth.email.isEmpty ? 'Farmer' : auth.email),
              subtitle: Text(auth.demo ? 'Demo session' : 'Signed in'),
              trailing: TextButton(
                onPressed: () => ref.read(authProvider.notifier).logout(),
                child: const Text('Sign out'),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Column(
              children: const [
                ListTile(leading: Icon(Icons.agriculture_outlined), title: Text('Green Valley Farm'), subtitle: Text('2 fields · since 2024')),
                Divider(height: 1),
                ListTile(leading: Icon(Icons.grid_on_outlined), title: Text('FIELD_001 — North plot'), subtitle: Text('Tomato · sowing Mar 12')),
                Divider(height: 1),
                ListTile(leading: Icon(Icons.router_outlined), title: Text('AGRO_NODE_001'), subtitle: Text('STM32 + ESP32 + cellular')),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Connection', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                  const SizedBox(height: 12),
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Demo mode'),
                    subtitle: const Text('Labeled demo data, works fully offline'),
                    value: cfg.demoMode,
                    onChanged: (v) => ref.read(appConfigProvider.notifier).setDemoMode(v),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: urlCtrl,
                    keyboardType: TextInputType.url,
                    decoration: const InputDecoration(
                      labelText: 'Backend base URL',
                      hintText: 'http://192.168.1.10:8000',
                      prefixIcon: Icon(Icons.dns_outlined),
                    ),
                  ),
                  const SizedBox(height: 8),
                  FilledButton.tonal(
                    onPressed: () {
                      ref.read(appConfigProvider.notifier).setBaseUrl(urlCtrl.text);
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Backend URL saved. Turn demo mode off to use it.')),
                      );
                    },
                    child: const Text('Save backend URL'),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Emulator: http://10.0.2.2:8000 · Physical phone: your PC’s LAN IP. Keys/secrets are never stored in the app.',
                    style: TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
