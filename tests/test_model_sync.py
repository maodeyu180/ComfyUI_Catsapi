"""Standard-library tests with mocked ComfyUI media and CatsAPI requests."""
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("catsapi_test_package", ROOT / "__init__.py",
                                            submodule_search_locations=[str(ROOT)])
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
nodes = sys.modules[f"{spec.name}.nodes"]
client = sys.modules[f"{spec.name}.catsapi_client"]
image_utils = sys.modules[f"{spec.name}.image_utils"]


def fake_images(images, *, max_images, name_prefix):
    images = images or []
    if len(images) > max_images:
        raise ValueError("too many references")
    return [{"name": name} for name in images]


class ModelSyncTests(unittest.TestCase):
    def setUp(self):
        self.network = patch.object(client, "request_json", side_effect=AssertionError("network forbidden"))
        self.network.start()
        self.addCleanup(self.network.stop)

    def test_node_registration_defaults_and_old_workflows(self):
        self.assertEqual(len(package.NODE_CLASS_MAPPINGS), 12)
        old_keys = {"CatsAPIGPTImage2", "CatsAPINanoBanana2", "CatsAPINanoBananaPro", "CatsAPIFLUX2Pro",
                    "CatsAPIGrokImage", "CatsAPISeedance20", "CatsAPIGrokImageVideo"}
        self.assertTrue(old_keys <= set(package.NODE_CLASS_MAPPINGS))
        self.assertEqual(set(package.NODE_CLASS_MAPPINGS), set(package.NODE_DISPLAY_NAME_MAPPINGS))
        for node_class in package.NODE_CLASS_MAPPINGS.values():
            required = node_class.INPUT_TYPES()["required"]
            values = {key: info[1]["default"] for key, info in required.items()}
            for kind, options in required.values():
                if isinstance(kind, list):
                    self.assertIn(options["default"], kind)
            with patch.object(nodes, "_generate_image", return_value="image") as image, \
                 patch.object(nodes, "_generate_video", return_value="video") as video:
                node_class().generate(**values)
            call = image.call_args or video.call_args
            self.assertFalse(call.kwargs["params"]["rewritePrompt"])
            if call.kwargs["model"] in ("nanoBanana2", "nanoBananaPro"):
                self.assertIs(call.kwargs["params"]["enableWebSearch"], True)

    def test_new_sizes_defaults_and_reference_limits(self):
        self.assertEqual(len(nodes.IMAGE_SIZES_GPT2), 20)
        self.assertIn("2688x1152", nodes.IMAGE_SIZES_GPT2)
        for node_class, maximum in ((nodes.CatsAPIGPTImage2, 16), (nodes.CatsAPINanoBanana2, 14),
                                    (nodes.CatsAPINanoBananaPro, 4), (nodes.CatsAPIFLUX2Pro, 3),
                                    (nodes.CatsAPIGrokImage, 1), (nodes.CatsAPIGrokImage2, 1),
                                    (nodes.CatsAPISeedream5Lite, 4), (nodes.CatsAPISeedream5Pro, 4)):
            values = {key: info[1]["default"] for key, info in node_class.INPUT_TYPES()["required"].items()}
            with patch.object(nodes, "_generate_image") as generate:
                node_class().generate(**values)
            self.assertEqual(generate.call_args.kwargs["max_reference_images"], maximum)
        for node_class, resolution in ((nodes.CatsAPISeedance20, "480p"), (nodes.CatsAPISeedance20Mini, "480p"),
                                       (nodes.CatsAPIGrokImageVideo, "720p")):
            inputs = node_class.INPUT_TYPES()["required"]
            self.assertEqual(inputs["resolution"][1]["default"], resolution)
            self.assertEqual(inputs["duration"][1]["default"], "8")

    def test_web_search_can_be_disabled(self):
        for node_class in (nodes.CatsAPINanoBanana2, nodes.CatsAPINanoBananaPro):
            values = {key: info[1]["default"] for key, info in node_class.INPUT_TYPES()["required"].items()}
            with patch.object(nodes, "_generate_image") as generate:
                node_class().generate(**values, enable_web_search=False)
            self.assertIs(generate.call_args.kwargs["params"]["enableWebSearch"], False)

    def test_seedance_combines_legacy_inputs_without_changing_output(self):
        result = {"id": "mock-task", "cost": 7, "result_video": {"url": "https://example.invalid/video.mp4"}}
        with patch.object(nodes, "tensor_to_image_inputs", side_effect=fake_images), \
             patch.object(nodes, "preview_cost", return_value={"total_cost": 7, "sufficient": True}), \
             patch.object(nodes, "submit_task", return_value={"id": "mock-task"}) as submit, \
             patch.object(nodes, "poll_task", return_value=result), \
             patch.object(nodes, "_output_path", return_value=Path("result.mp4")), \
             patch.object(nodes, "download_file", return_value=Path("result.mp4")):
            output = nodes.CatsAPISeedance20().generate(
                "test", "480p", "8", "16:9", 10, start_image=["start"],
                reference_images=["ref1", "ref2"], end_image=["end"], api_key_override="test-only-value")
        payload = submit.call_args.kwargs
        self.assertEqual(payload["params"]["inputMode"], "reference")
        self.assertEqual(payload["files"], {"referenceImages": [
            {"name": "start"}, {"name": "ref1"}, {"name": "ref2"}, {"name": "end"}]})
        self.assertEqual(output[:3], ("result.mp4", 7, "mock-task"))
        self.assertNotIn("test-only-value", output[3])
        self.assertNotIn("example.invalid", output[3])

    def test_seedance_total_limit_rejects_before_preview_or_submit(self):
        with patch.object(nodes, "tensor_to_image_inputs", side_effect=fake_images), \
             patch.object(nodes, "preview_cost") as preview, patch.object(nodes, "submit_task") as submit, \
             self.assertRaises(nodes.CatsAPIError):
            nodes.CatsAPISeedance20().generate("test", "480p", "8", "16:9", 0,
                                               start_image=["start"], reference_images=["a", "b", "c", "d"])
        preview.assert_not_called()
        submit.assert_not_called()

    def test_spending_guard_and_balance_prevent_submission(self):
        for preview_result in ({"total_cost": 20, "sufficient": True},
                               {"total_cost": 5, "sufficient": False, "balance": 0}, {},
                               {"total_cost": "5", "sufficient": True},
                               {"total_cost": 5}, {"total_cost": True, "sufficient": True},
                               {"total_cost": float("nan"), "sufficient": True},
                               {"total_cost": -1, "sufficient": True}):
            with patch.object(nodes, "tensor_to_image_inputs", side_effect=fake_images), \
                 patch.object(nodes, "preview_cost", return_value=preview_result), \
                 patch.object(nodes, "submit_task") as submit, self.assertRaises(nodes.CatsAPIError):
                nodes.CatsAPISeedance20().generate("test", "480p", "8", "16:9", 10)
            submit.assert_not_called()

    def test_image_tensor_contract_with_mocked_media(self):
        tensor = object()
        result = {"id": "mock-task", "cost": 3, "result_images": [{"url": "https://example.invalid/a.png"}]}
        with patch.object(nodes, "tensor_to_image_inputs", side_effect=fake_images), \
             patch.object(nodes, "preview_cost", return_value={"total_cost": 3, "sufficient": True}) as preview, \
             patch.object(nodes, "submit_task", return_value={"id": "mock-task"}) as submit, \
             patch.object(nodes, "poll_task", return_value=result), \
             patch.object(nodes, "_output_path", return_value=Path("result.png")), \
             patch.object(nodes, "download_file", return_value=Path("result.png")), \
             patch.object(nodes, "image_paths_to_tensor", return_value=tensor):
            output = nodes.CatsAPIGPTImage2().generate("test", "2688x1152", "auto", 1, 10,
                                                    reference_image=[f"image-{i}" for i in range(16)])
        self.assertEqual(len(submit.call_args.kwargs["images"]), 16)
        self.assertEqual(preview.call_args.kwargs["resolution"], "2688x1152")
        self.assertIs(output[0], tensor)
        self.assertEqual(json.loads(output[1]), ["result.png"])

    def test_image_converter_rejects_oversized_batch_without_truncating(self):
        array = Mock()
        array.ndim = 4
        array.__len__ = Mock(return_value=17)
        numpy = types.ModuleType("numpy")
        numpy.asarray = Mock(return_value=array)
        pil = types.ModuleType("PIL")
        pil.Image = Mock()
        with patch.dict(sys.modules, {"numpy": numpy, "PIL": pil}), self.assertRaisesRegex(ValueError, "maximum 16"):
            image_utils.tensor_to_image_inputs(object(), max_images=16, name_prefix="test")

    def test_poll_failure_and_timeout_are_bounded(self):
        with patch.object(client, "get_json", return_value={"status": "failed", "error_message": "mock"}), \
             patch.object(client.time, "sleep"), self.assertRaises(client.CatsAPIError):
            client.poll_task("mock-task")
        with patch.object(client, "get_json", return_value={"status": "processing"}), \
             patch.object(client.time, "sleep"), patch.object(client.time, "time", side_effect=[0, 2]), \
             self.assertRaises(client.CatsAPIError):
            client.poll_task("mock-task", timeout=1)

    def test_new_image_nodes_exact_fields_seed_and_reference_limits(self):
        for node_class, key in ((nodes.CatsAPISeedream5Lite, "seedream5Lite"),
                                (nodes.CatsAPISeedream5Pro, "seedream5Pro")):
            for seed in (-1, 0, 42):
                with patch.object(nodes, "_generate_image") as generate:
                    node_class().generate("test", "landscape_16_9", 4, 50, seed=seed)
                payload = generate.call_args.kwargs
                self.assertEqual(payload["model"], key)
                expected = {"imageSize": "landscape_16_9", "rewritePrompt": False}
                if seed >= 0:
                    expected["seed"] = seed
                self.assertEqual(payload["params"], expected)
                self.assertEqual(payload["cost_resolution"], "landscape_16_9")
                self.assertEqual(payload["max_reference_images"], 4)
                self.assertEqual(payload["num_images"], 4)
        with patch.object(nodes, "_generate_image") as generate:
            nodes.CatsAPIGrokImage2().generate("test", "9:16", 2, 20)
        self.assertEqual(generate.call_args.kwargs["model"], "grokImagineImage2")
        self.assertEqual(generate.call_args.kwargs["params"], {"aspectRatio": "9:16", "rewritePrompt": False})

    def test_new_video_widgets_and_payloads(self):
        for node_class, key in ((nodes.CatsAPISeedance20, "seedance20"),
                                (nodes.CatsAPISeedance20Mini, "seedance20Mini")):
            with patch.object(nodes, "_generate_video") as generate:
                node_class().generate("test", "720p", "15", "9:16", 100)
            payload = generate.call_args.kwargs
            self.assertEqual(payload["model"], key)
            self.assertEqual(payload["cost_duration"], "15")
            self.assertEqual(payload["cost_resolution"], "720p")
            if key == "seedance20Mini":
                self.assertNotIn("mode", payload["params"])
                self.assertIsNone(payload["cost_mode"])
            else:
                self.assertEqual(payload["params"]["mode"], "fast")
                self.assertEqual(payload["cost_mode"], "fast")
        inputs = nodes.CatsAPIGeminiOmniFlash.INPUT_TYPES()["required"]
        self.assertEqual(inputs["duration"][0], [str(n) for n in range(5, 11)])
        self.assertEqual(inputs["aspect_ratio"][0], ["16:9", "9:16"])
        self.assertNotIn("resolution", inputs)
        self.assertNotIn("mode", inputs)
        with patch.object(nodes, "_generate_video") as generate:
            nodes.CatsAPIGeminiOmniFlash().generate("test", "10", "9:16", 100)
        payload = generate.call_args.kwargs
        self.assertEqual(payload["model"], "geminiOmniFlash")
        self.assertEqual(payload["params"], {"duration": "10", "aspectRatio": "9:16", "rewritePrompt": False})
        self.assertEqual(payload["cost_duration"], "10")
        self.assertNotIn("cost_resolution", payload)
        self.assertNotIn("cost_mode", payload)

    def test_mini_merges_reference_inputs_and_omni_keeps_start_frame(self):
        result = {"id": "mock-task", "cost": 7, "result_video": {"url": "https://example.invalid/video.mp4"}}
        for mini in (True, False):
            with patch.object(nodes, "tensor_to_image_inputs", side_effect=fake_images), \
                 patch.object(nodes, "preview_cost", return_value={"total_cost": 7, "sufficient": True}) as preview, \
                 patch.object(nodes, "submit_task", return_value={"id": "mock-task"}) as submit, \
                 patch.object(nodes, "poll_task", return_value=result), \
                 patch.object(nodes, "_output_path", return_value=Path("result.mp4")), \
                 patch.object(nodes, "download_file", return_value=Path("result.mp4")):
                if mini:
                    output = nodes.CatsAPISeedance20Mini().generate(
                        "test", "720p", "6", "9:16", 10, start_image=["start"],
                        reference_images=["a", "b"], end_image=["end"])
                else:
                    output = nodes.CatsAPIGeminiOmniFlash().generate("test", "6", "9:16", 10, start_image=["start"])
            submit.assert_called_once()
            payload = submit.call_args.kwargs
            self.assertNotIn("mode", payload["params"])
            self.assertTrue(preview.call_args.kwargs["has_image_input"])
            self.assertEqual(preview.call_args.kwargs["duration"], "6")
            self.assertIsNone(preview.call_args.kwargs["mode"])
            if mini:
                self.assertEqual(payload["files"]["referenceImages"], [{"name": n} for n in ("start", "a", "b", "end")])
                self.assertEqual(list(payload["files"]), ["referenceImages"])
            else:
                self.assertEqual(payload["files"], {"startFrame": {"name": "start"}})
                self.assertIsNone(preview.call_args.kwargs["resolution"])
            self.assertEqual(output[:3], ("result.mp4", 7, "mock-task"))

    def test_mini_oversized_references_reject_before_charge(self):
        with patch.object(nodes, "tensor_to_image_inputs", side_effect=fake_images), \
             patch.object(nodes, "preview_cost") as preview, patch.object(nodes, "submit_task") as submit, \
             self.assertRaises(nodes.CatsAPIError):
            nodes.CatsAPISeedance20Mini().generate("test", "480p", "8", "16:9", 0,
                                                   start_image=["start"], reference_images=["a", "b", "c", "d"])
        preview.assert_not_called()
        submit.assert_not_called()

    def test_new_image_nodes_cost_and_submission_use_same_parameters(self):
        result = {"id": "mock-task", "cost": 9, "result_images": [{"url": "https://example.invalid/a.png"}]}
        for node_class in (nodes.CatsAPISeedream5Lite, nodes.CatsAPISeedream5Pro, nodes.CatsAPIGrokImage2):
            seedream = node_class is not nodes.CatsAPIGrokImage2
            with patch.object(nodes, "tensor_to_image_inputs", side_effect=fake_images), \
                 patch.object(nodes, "preview_cost", return_value={"total_cost": 9, "sufficient": True}) as preview, \
                 patch.object(nodes, "submit_task", return_value={"id": "mock-task"}) as submit, \
                 patch.object(nodes, "poll_task", return_value=result), \
                 patch.object(nodes, "_output_path", return_value=Path("result.png")), \
                 patch.object(nodes, "download_file", return_value=Path("result.png")), \
                 patch.object(nodes, "image_paths_to_tensor", return_value=object()):
                node_class().generate("test", "portrait_16_9" if seedream else "9:16", 2, 10,
                                      reference_image=["ref"])
            submit.assert_called_once()
            request, quote = submit.call_args.kwargs, preview.call_args.kwargs
            self.assertEqual(request["num_images"], quote["num_images"])
            self.assertTrue(quote["has_image_input"])
            self.assertEqual(request["model"], quote["model"])
            self.assertEqual(quote["resolution"], "portrait_16_9" if seedream else None)


if __name__ == "__main__":
    unittest.main()
