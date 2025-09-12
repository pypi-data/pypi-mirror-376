wagtail_3display
=============

Wagtail 3D model viewer block using <https://threejs.org/>.

Installation
------------

1. Install the package using pip:

   ```bash
   pip install wagtail-3display
   ```

2. Add `wagtail_3display` to your `INSTALLED_APPS` in `settings.py`:

   ```python
    INSTALLED_APPS = [
         ...
         'wagtail_3display',
         ...
    ]
    ```

3. Run migrations to create necessary database tables:

    ```bash
    python manage.py migrate wagtail_3display
    ```

4. Collect static files:

    ```bash
    python manage.py collectstatic
    ```

5. Ensure you have the necessary static files in your templates:

    ```django
    <script src="{% static 'wagtail_3display/js/3display.js' %}"></script>
    ```

Usage
-----

1. In your Wagtail admin, add a new block of type "ThreeDisplayBlock" to your StreamField.

2. Upload a 3D model file (e.g., .glb, .gltf) using the block's file chooser.

3. Save the page and view it on the frontend to see the 3D model rendered.

