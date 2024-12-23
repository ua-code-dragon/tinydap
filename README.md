# tinydap
Testbed for directory tree and DAP backend concept

Here, we demonstrate the proof of concept of several approaches in backend design and directory tree architecture for encapsulating objects and their rights by subjects.

1. Using flask login extended with RSA form encryption for secure transmission and fooling interceptors.

2. Extremely simplified mechanism for managing backend background processes using FIFO as a message broker. Allows asynchronous tasks in a single server scope with many workers without using Celery and similar cumbersome services.

3. A catalogue tree scheme inspired by DAP is demonstrated. The tree allows for the arbitrary nesting of users, groups, documents, and folders, as well as the arbitrary distribution and inheritance of rights.


