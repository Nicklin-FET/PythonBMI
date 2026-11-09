import unittest

from app import app, bmi_guidance


class BmiAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_initial_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("了解自己的<br><em>健康狀況。</em>", page)
        self.assertIn("計算你的 BMI", page)
        self.assertIn('id="name" name="name" type="text" autocomplete="name"', page)
        self.assertNotIn('class="bmi-chart"', page)

    def test_calculation_and_advice(self):
        response = self.client.post("/", data={"height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertIn("22.5", page)
        self.assertIn("健康體位", page)
        self.assertIn("維持均衡飲食", page)
        self.assertIn("<p>維持均衡飲食", page)

    def test_name_is_trimmed_and_included_in_advice(self):
        response = self.client.post("/", data={"name": "  王小明  ", "height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('value="王小明"', page)
        self.assertIn("<p>王小明，維持均衡飲食", page)
        self.assertIn("22.5", page)

    def test_blank_name_keeps_generic_advice(self):
        for name in ["", "   "]:
            with self.subTest(name=name):
                response = self.client.post("/", data={"name": name, "height": "170", "weight": "65"})
                self.assertEqual(response.status_code, 200)
                self.assertIn("<p>維持均衡飲食", response.get_data(as_text=True))

    def test_name_is_preserved_when_measurements_are_invalid(self):
        response = self.client.post("/", data={"name": "王小明", "height": "", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('value="王小明"', page)
        self.assertIn('aria-invalid="true"', page)
        self.assertNotIn("YOUR RESULT", page)

    def test_name_is_escaped_in_input_and_advice(self):
        response = self.client.post("/", data={"name": '<script>alert("name")</script>', "height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("<script>", page)
        self.assertIn('value="&lt;script&gt;alert(&#34;name&#34;)&lt;/script&gt;"', page)
        self.assertIn("<p>&lt;script&gt;alert(&#34;name&#34;)&lt;/script&gt;，維持均衡飲食", page)

    def test_chart_position_and_categories(self):
        for bmi, category, position in [
            (18.4, "體重過輕", 46.0),
            (18.5, "健康體位", 46.25),
            (24.0, "體重過重", 60.0),
            (27.0, "肥胖", 67.5),
            (40.0, "肥胖", 100.0),
            (50.0, "肥胖", 100.0),
            (0.1, "體重過輕", 0.25),
        ]:
            with self.subTest(bmi=bmi):
                response = self.client.post("/", data={"height": "100", "weight": str(bmi)})
                page = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn('class="bmi-chart"', page)
                self.assertIn(f'aria-label="BMI {bmi:.1f}，{category}。', page)
                self.assertIn(f'class="bmi-chart-marker" style="left: {position}%;"', page)
                for label in ["體重過輕", "健康體位", "體重過重", "肥胖", "40+"]:
                    self.assertIn(label, page)

    def test_taiwan_adult_thresholds(self):
        for bmi, category in [
            (18.4, "體重過輕"),
            (18.5, "健康體位"),
            (23.9, "健康體位"),
            (24.0, "體重過重"),
            (26.9, "體重過重"),
            (27.0, "肥胖"),
        ]:
            with self.subTest(bmi=bmi):
                self.assertEqual(bmi_guidance(bmi)["label"], category)

    def test_invalid_fields_do_not_produce_result(self):
        for height, weight in [("", "65"), ("0", "65"), ("abc", "65"), ("170", "-2"), ("inf", "65"), ("170", "nan"), ("1e-300", "65"), ("1e308", "65"), ("1", "1e308")]:
            with self.subTest(height=height, weight=weight):
                response = self.client.post("/", data={"height": height, "weight": weight})
                page = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn('aria-invalid="true"', page)
                self.assertNotIn("YOUR RESULT", page)
                self.assertNotIn('class="bmi-chart"', page)

    def test_input_is_escaped(self):
        response = self.client.post("/", data={"height": '<script>alert(1)</script>', "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertNotIn("<script>", page)
        self.assertIn("請輸入大於 0", page)


if __name__ == "__main__":
    unittest.main()
