<script setup lang="ts">
import { ArrowLeftIcon } from '@heroicons/vue/24/outline';
</script>

<template>
  <div class="min-h-screen bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-4xl mx-auto">
      <!-- Back Button -->
      <a
        href="javascript:history.back()"
        class="inline-flex items-center text-blue-400 hover:text-blue-300 mb-6"
      >
        <ArrowLeftIcon class="h-5 w-5 mr-2" />
        Back
      </a>

      <!-- Header -->
      <div class="bg-gray-800 rounded-lg shadow-lg p-8 mb-8">
        <h1 class="text-4xl font-bold text-white mb-4">Terms and Conditions</h1>
        <p class="text-gray-400">Last updated: {{ new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) }}</p>
      </div>

      <!-- Content -->
      <div class="bg-gray-800 rounded-lg shadow-lg p-8 space-y-8 text-gray-300">

        <!-- 1. Introduction -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">1. Introduction</h2>
          <p class="mb-4">
            Welcome to Diagramik. These Terms and Conditions ("Terms") govern your access to and use of
            Diagramik (the "Service"), a web-based diagramming application. By accessing or using the
            Service, you agree to be bound by these Terms.
          </p>
          <p>
            If you do not agree to these Terms, you may not access or use the Service.
          </p>
        </section>

        <!-- 2. Service Provider -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">2. Service Provider and Data Controller</h2>
          <div class="bg-blue-500/10 border border-blue-500 rounded-lg p-6 mb-4">
            <p class="mb-2"><strong class="text-white">Name:</strong> Krzysztof Watras (operating as an individual)</p>
            <p class="mb-2"><strong class="text-white">Email:</strong> chris.watras@gmail.com</p>
            <p><strong class="text-white">Data Storage Region:</strong> European Union (EU)</p>
          </div>
          <p>
            Krzysztof Watras is the sole owner and operator of this Service and acts as the data
            controller for all personal data processed through the Service. This Service is operated
            as an individual project, not as a company or legal entity.
          </p>
        </section>

        <!-- 3. Data Processing and Privacy -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">3. Data Processing and Privacy</h2>

          <h3 class="text-xl font-semibold text-white mb-3 mt-6">3.1 Data We Collect</h3>
          <p class="mb-3">When you use Diagramik, we collect and process the following types of data:</p>
          <ul class="list-disc list-inside space-y-2 ml-4 mb-4">
            <li><strong class="text-white">Account Information:</strong> Email address, name (optional), and password (encrypted)</li>
            <li><strong class="text-white">Usage Data:</strong> Diagrams you create, edit, and store within the Service</li>
            <li><strong class="text-white">Technical Data:</strong> IP address, browser type, device information, and access logs</li>
            <li><strong class="text-white">Authentication Data:</strong> When using Google OAuth, we receive your Google profile information (name, email)</li>
          </ul>

          <h3 class="text-xl font-semibold text-white mb-3 mt-6">3.2 How We Use Your Data</h3>
          <p class="mb-3">Your data is processed for the following purposes:</p>
          <ul class="list-disc list-inside space-y-2 ml-4 mb-4">
            <li>Providing and maintaining the Service</li>
            <li>Creating and managing your user account</li>
            <li>Storing and synchronizing your diagrams</li>
            <li>Communicating with you about the Service (e.g., verification emails, important updates)</li>
            <li>Improving and optimizing the Service</li>
            <li>Ensuring security and preventing abuse</li>
          </ul>

          <h3 class="text-xl font-semibold text-white mb-3 mt-6">3.3 Data Storage and Security</h3>
          <p class="mb-4">
            All user data is stored on servers located within the European Union. We implement
            industry-standard security measures to protect your data, including:
          </p>
          <ul class="list-disc list-inside space-y-2 ml-4 mb-4">
            <li>Encrypted password storage using strong hashing algorithms</li>
            <li>HTTPS/TLS encryption for all data transmission</li>
            <li>Regular security updates and monitoring</li>
            <li>Access controls and authentication mechanisms</li>
          </ul>
          <p>
            However, no method of transmission over the Internet or electronic storage is 100% secure.
            While we strive to protect your data, we cannot guarantee absolute security.
          </p>

          <h3 class="text-xl font-semibold text-white mb-3 mt-6">3.4 Data Retention</h3>
          <p>
            We retain your personal data for as long as your account is active or as needed to provide
            you with the Service. If you delete your account, we will delete your personal data within
            30 days, except where we are required to retain it for legal or regulatory purposes.
          </p>
        </section>

        <!-- 4. Your Rights (GDPR) -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">4. Your Rights Under GDPR</h2>
          <p class="mb-4">
            As a user in the European Union, you have the following rights under the General Data
            Protection Regulation (GDPR):
          </p>
          <ul class="list-disc list-inside space-y-2 ml-4">
            <li><strong class="text-white">Right of Access:</strong> You can request a copy of your personal data</li>
            <li><strong class="text-white">Right to Rectification:</strong> You can request corrections to inaccurate data</li>
            <li><strong class="text-white">Right to Erasure:</strong> You can request deletion of your personal data ("right to be forgotten")</li>
            <li><strong class="text-white">Right to Restriction:</strong> You can request restriction of processing in certain circumstances</li>
            <li><strong class="text-white">Right to Data Portability:</strong> You can request your data in a machine-readable format</li>
            <li><strong class="text-white">Right to Object:</strong> You can object to certain types of processing</li>
            <li><strong class="text-white">Right to Withdraw Consent:</strong> You can withdraw consent at any time</li>
          </ul>
          <p class="mt-4">
            To exercise any of these rights, please contact us at <a href="mailto:chris.watras@gmail.com" class="text-blue-400 hover:text-blue-300 underline">chris.watras@gmail.com</a>.
          </p>
        </section>

        <!-- 5. Use of the Service -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">5. Acceptable Use</h2>

          <h3 class="text-xl font-semibold text-white mb-3 mt-6">5.1 Permitted Use</h3>
          <p class="mb-4">
            You may use Diagramik to create, edit, store, and share diagrams for personal, educational,
            or commercial purposes, subject to these Terms.
          </p>

          <h3 class="text-xl font-semibold text-white mb-3 mt-6">5.2 Prohibited Use</h3>
          <p class="mb-3">You agree NOT to:</p>
          <ul class="list-disc list-inside space-y-2 ml-4">
            <li>Use the Service for any illegal or unauthorized purpose</li>
            <li>Violate any laws in your jurisdiction (including but not limited to copyright laws)</li>
            <li>Transmit any malicious code, viruses, or harmful software</li>
            <li>Attempt to gain unauthorized access to the Service or its systems</li>
            <li>Interfere with or disrupt the Service or servers/networks connected to the Service</li>
            <li>Use automated means (bots, scrapers) to access the Service without permission</li>
            <li>Impersonate any person or entity or misrepresent your affiliation</li>
            <li>Upload or share content that infringes on intellectual property rights</li>
            <li>Upload or share content that is offensive, abusive, or violates others' rights</li>
          </ul>
        </section>

        <!-- 6. Account Responsibilities -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">6. Account Responsibilities</h2>
          <p class="mb-3">You are responsible for:</p>
          <ul class="list-disc list-inside space-y-2 ml-4">
            <li>Maintaining the confidentiality of your account credentials</li>
            <li>All activities that occur under your account</li>
            <li>Notifying us immediately of any unauthorized use of your account</li>
            <li>Ensuring that your account information is accurate and up to date</li>
          </ul>
          <p class="mt-4">
            We reserve the right to suspend or terminate accounts that violate these Terms or
            engage in suspicious activity.
          </p>
        </section>

        <!-- 7. Intellectual Property -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">7. Intellectual Property</h2>

          <h3 class="text-xl font-semibold text-white mb-3 mt-6">7.1 Service Ownership</h3>
          <p class="mb-4">
            The Service, including its design, code, features, and functionality, is owned by
            Krzysztof Watras and is protected by copyright, trademark, and other intellectual
            property laws.
          </p>

          <h3 class="text-xl font-semibold text-white mb-3 mt-6">7.2 Your Content</h3>
          <p class="mb-4">
            You retain all rights to the diagrams and content you create using the Service. By using
            the Service, you grant us a limited license to store, display, and process your content
            solely for the purpose of providing the Service to you.
          </p>
          <p>
            We do not claim ownership of your diagrams or use them for any purpose other than
            operating the Service.
          </p>
        </section>

        <!-- 8. Service Availability -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">8. Service Availability and Disclaimers</h2>
          <p class="mb-4">
            The Service is provided "as is" and "as available" without warranties of any kind, either
            express or implied. We do not guarantee that:
          </p>
          <ul class="list-disc list-inside space-y-2 ml-4">
            <li>The Service will be uninterrupted, secure, or error-free</li>
            <li>The Service will meet your specific requirements</li>
            <li>Any errors or defects will be corrected</li>
            <li>The Service will be available at all times</li>
          </ul>
          <p class="mt-4">
            We reserve the right to modify, suspend, or discontinue the Service (or any part thereof)
            at any time, with or without notice.
          </p>
        </section>

        <!-- 9. Limitation of Liability -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">9. Limitation of Liability</h2>
          <p class="mb-4">
            To the maximum extent permitted by law, Krzysztof Watras shall not be liable for any
            indirect, incidental, special, consequential, or punitive damages, including but not
            limited to:
          </p>
          <ul class="list-disc list-inside space-y-2 ml-4">
            <li>Loss of data or diagrams</li>
            <li>Loss of profits or revenue</li>
            <li>Loss of business opportunities</li>
            <li>Service interruptions or downtime</li>
          </ul>
          <p class="mt-4">
            Our total liability for any claims arising from your use of the Service shall not exceed
            the amount you paid for the Service in the 12 months preceding the claim (or €100 if no
            fees were paid).
          </p>
        </section>

        <!-- 10. Third-Party Services -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">10. Third-Party Services</h2>
          <p class="mb-4">
            The Service may integrate with third-party services such as Google OAuth for authentication.
            Your use of these third-party services is subject to their respective terms and privacy
            policies. We are not responsible for the practices or content of third-party services.
          </p>
        </section>

        <!-- 11. Changes to Terms -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">11. Changes to These Terms</h2>
          <p class="mb-4">
            We reserve the right to modify these Terms at any time. If we make material changes, we
            will notify you by email or through a prominent notice on the Service. Your continued use
            of the Service after changes become effective constitutes acceptance of the modified Terms.
          </p>
          <p>
            We encourage you to review these Terms periodically.
          </p>
        </section>

        <!-- 12. Termination -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">12. Termination</h2>
          <p class="mb-4">
            You may terminate your account at any time by contacting us or using the account deletion
            feature (if available). We may terminate or suspend your account immediately, without prior
            notice, if you breach these Terms or engage in conduct that we deem harmful to the Service
            or other users.
          </p>
          <p>
            Upon termination, your right to use the Service will cease immediately, and we may delete
            your account and data.
          </p>
        </section>

        <!-- 13. Governing Law -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">13. Governing Law and Dispute Resolution</h2>
          <p class="mb-4">
            These Terms shall be governed by and construed in accordance with the laws of Poland,
            without regard to its conflict of law provisions.
          </p>
          <p>
            Any disputes arising from these Terms or your use of the Service shall be resolved in
            the courts of Poland. If you are a consumer in the EU, you may also have the right to
            bring disputes in your country of residence.
          </p>
        </section>

        <!-- 14. Contact Information -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">14. Contact Information</h2>
          <p class="mb-4">
            If you have any questions, concerns, or requests regarding these Terms or the Service,
            please contact:
          </p>
          <div class="bg-gray-700 rounded-lg p-6">
            <p class="mb-2"><strong class="text-white">Krzysztof Watras</strong></p>
            <p class="mb-2">Email: <a href="mailto:chris.watras@gmail.com" class="text-blue-400 hover:text-blue-300 underline">chris.watras@gmail.com</a></p>
          </div>
        </section>

        <!-- 15. Severability -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">15. Severability</h2>
          <p>
            If any provision of these Terms is found to be unenforceable or invalid, that provision
            shall be limited or eliminated to the minimum extent necessary so that these Terms shall
            otherwise remain in full force and effect.
          </p>
        </section>

        <!-- 16. Entire Agreement -->
        <section>
          <h2 class="text-2xl font-bold text-white mb-4">16. Entire Agreement</h2>
          <p>
            These Terms constitute the entire agreement between you and Krzysztof Watras regarding
            the use of the Service and supersede all prior agreements and understandings.
          </p>
        </section>

      </div>

      <!-- Footer -->
      <div class="mt-8 text-center text-gray-500 text-sm">
        <p>By using Diagramik, you acknowledge that you have read, understood, and agree to be bound by these Terms and Conditions.</p>
      </div>
    </div>
  </div>
</template>
